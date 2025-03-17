from datetime import datetime
import json
from ninja import Router, Schema
from django.contrib import auth
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django import forms
from django.http import HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import get_list_or_404, get_object_or_404

from django.contrib.auth.models import User
from ninja import ModelSchema
from typing import List
import stat
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from .models import Graph, UserDashboard

import pandas as pd
from .utils import get_object_or_none, init_dashboards, remove_custom_query, update_default_query, create_custom_query

router = Router()

class Error(Schema):
    message: str

token = 'iAW7kXdT1XvOpOc7fZyPzXLC5N3vBJgkjb8SnIZ1q3ec6CAhLPMbtSY607wxIAgXrcUCt_HqpALVP3p0_375-w=='
url = "http://localhost:8086"
org = "atsys"

influx = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

@router.get('/bucket')
def bucket_list(request):
    api = influx.buckets_api()
    buckets = api.find_buckets().buckets

    user_buckets = []
    for bucket in buckets:
        if bucket.type == 'user':
            user_buckets.append(bucket.name)
    return user_buckets

@router.get('/measurement')
def measurement_list(request, bucket: str):
    result = []
    query_api = influx.query_api()
    query = f"""import \"regexp\"
        from(bucket: \"{bucket}\")
        |> range(start: -10000d, stop: now())
        |> filter(fn: (r) => true)
        |> keep(columns: [\"_measurement\"])
        |> group()
        |> distinct(column: \"_measurement\")
        |> limit(n: 1000)
        |> sort()"""
    tables = query_api.query(query)
    for table in tables:
        for record in table.records:
            result.append(record.values['_value'])
    return result

@router.get('/field')
def field_list(request, bucket: str, measurement: str):
    result = []
    query_api = influx.query_api()
    query = f"""import \"regexp\"
        from(bucket: \"{bucket}\")
        |> range(start: -10000d, stop: now())
        |> filter(fn: (r) => (r[\"_measurement\"] == \"{measurement}\"))
        |> keep(columns: [\"_field\"])
        |> group()
        |> distinct(column: \"_field\")
        |> limit(n: 1000)
        |> sort()"""
    tables = query_api.query(query)
    for table in tables:
        for col in table.columns:
            result.append({
                'bucket': bucket,
                'measurement': measurement,
                'data_type': col.data_type,
                'name': ''
            })
        for index in range(len(table.records)):
            result[index]['name'] = table.records[index]['_value']
    return result

@router.get('/query')
def query_sql(request, sql: str):
    result = []
    query_api = influx.query_api()
    tables = query_api.query(sql)
    for table in tables:
        for col in table.columns:
            print(col)
        for record in table.records:
            result.append({
                "_measurement": record['_measurement'],
                "_field": record['_field'],
                "_value": record['_value'],
                "_start": record['_start'],
                "_stop": record['_stop'],
                "_time": record['_time'],
            })
    return result


@router.get('/download')
def download_excel(request, sql: str):
    """
    Export influx query result as excel file.
    """
    result = []
    query_api = influx.query_api()
    tables = query_api.query(sql)
    for table in tables:
        for record in table.records:
            result.append([
                str(record['_measurement']),
                str(record['_field']),
                str(record['_value']),
                str(record['_start']),
                str(record['_stop']),
                str(record['_time'])
            ])
    columns = ["_measurement","_field","_value","_start","_stop","_time"]
    sheet1 = pd.DataFrame(result, columns=columns)

    # Generate file path with timestamped filename
    filename = "query-" + datetime.now().strftime("%Y%m%d%H%M%S")
    filepath = os.path.join(os.getcwd(), 'upload', 'export', f"{filename}.xlsx")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    os.chmod(os.path.dirname(filepath), 777)  # 设置为可读写执行权限

    # Write data to Excel file
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        sheet1.to_excel(writer, sheet_name="query")

    # 等待文件生成，每隔2秒检查一次，最多等待5次（10秒）
    max_attempts = 5
    attempts = 0
    while not os.path.exists(filepath) and attempts < max_attempts:
        time.sleep(2)
        attempts += 1

    # return the excel data as response
    def file_iterator():
        with open(filepath, 'rb') as file:
            while True:
                c = file.read(512)
                if c:
                    yield c
                else:
                    break
        
        # Delete the temporary file after sending it
        os.remove(filepath)
    response = StreamingHttpResponse(file_iterator())
    response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response['Content-Disposition'] = f"attachment;filename=\"{filename}.xlsx\""

    return response



@router.get('/query/graph')
def query_graph(request, sql: str, graph_type: str, start: str = "now-5y", end: str = "now"):
    # 1. Read config
    config = get_object_or_none(UserDashboard, user=request.user)
    if config is None:
        config = init_dashboards(request.user)

    result = []
    # 2. Update the dashboard graph
    result = update_default_query(sql, graph_type, start, end, config)
    if not result:
        return HttpResponseBadRequest(json.dumps({"message": "Get sql graph failed."}))

    # 3. Return the new url
    url = f"http://localhost:3000/d-solo/{config.default_dashboard_uid}/default?panelId=1"
    return url


class QueryParam(Schema):
    title: str
    query: str
    range_start: str
    range_end: str
    limit: int

@router.post('/graph')
def save_graph(request, payload: QueryParam):
    # 1. Read config
    config = get_object_or_none(UserDashboard, user=request.user)
    if config is None:
        config = init_dashboards(request.user)

    result = []
    # 2. Update the dashboard graph
    panel_index = create_custom_query(payload.query, payload.title, payload.range_start, payload.range_end, config)
    if not panel_index:
        return HttpResponseBadRequest(json.dumps({"message": "Get sql graph failed."}))
    panel = Graph.objects.create(
        user=request.user,
        dashboard_index=panel_index,
        title=payload.title,
        query=payload.query,
        range_start=payload.range_start,
        range_end=payload.range_end,
        limit=payload.limit
    )

    # 3. Return the new url
    url = f"http://localhost:3000/d-solo/{config.custom_dashboard_uid}/default?panelId={panel_index}"
    return url

@router.get('/graph')
def get_graphs(request):
    # 1. Read config
    config = get_object_or_none(UserDashboard, user=request.user)
    if config is None:
        config = init_dashboards(request.user)

    # 2.
    panels = get_list_or_404(Graph, user=request.user)
    # 3. Return the new url
    results = []
    for panel in panels:
        results.append({
            'id': panel.id,
            'title': panel.title,
            'dashboard_index': panel.dashboard_index,
            'query': panel.query,
            'range_start': panel.range_start,
            'range_end': panel.range_end,
            'limit': panel.limit,
            'created_at': panel.created_at,
            'url': f"http://localhost:3000/d-solo/{config.custom_dashboard_uid}/default?panelId={panel.dashboard_index}"
        })
    return results


@router.delete('/graph')
def delete_graph(request, id: int):
    # 1. Read config
    config = get_object_or_none(UserDashboard, user=request.user)
    if config is None:
        config = init_dashboards(request.user)

    panel = get_object_or_none(Graph, user=request.user, id=id)
    if panel is not None:
        dashboard_index = panel.dashboard_index
        remove_custom_query(dashboard_index, config)
        panel.delete()
        # update all other dashboard index
        toupdates = Graph.objects.filter(user=request.user,dashboard_index__gt=dashboard_index)
        for toupdate in toupdates:
            toupdate.dashboard_index -= 1
            toupdate.save()

    return {"message": "delete success"}