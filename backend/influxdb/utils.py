from ninja import Router, Schema
from django.conf import settings
from django import forms
from django.http import HttpResponseBadRequest
from django.shortcuts import _get_queryset


import json
from django.contrib.auth.models import User
import requests

from .models import UserDashboard


host = "http://localhost:3000"
datasource_name = "InfluxDB-m418"
headers = {
    'Content-type': 'application/json',
    'Authorization': 'Bearer glsa_q5V5U6avupwpr6mGVYQQ9hyNRH9kDu2u_22621679'
}

def get_object_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def fetch_dashboards():
    dashboards = []
    url = host + '/api/search?limit=1000'
    try:
        response = requests.get(url, headers=headers)
        dashboards = response.json()
        # get only type = dash-db
        dashboards = list(filter(lambda d: d["type"] == "dash-db", dashboards))
    except json.JSONDecodeError:
        print('Invalid JSON format')
    except KeyError:
        print('Invalid key')
    return dashboards

def fetch_default_dashboards():
    dashboards = []
    url = host + '/api/search?limit=1000&query=default'
    try:
        response = requests.get(url, headers=headers)
        dashboards = response.json()
        # get only type = dash-db
        dashboards = list(filter(lambda d: d["type"] == "dash-db", dashboards))
    except json.JSONDecodeError:
        print('Invalid JSON format')
    except KeyError:
        print('Invalid key')
    return dashboards

def fetch_dashboard(uid: str):
    meta = None
    url = host + f"/api/dashboards/uid/{uid}"
    try:
        response = requests.get(url, headers=headers)
        meta = response.json()
    except json.JSONDecodeError:
        print('Invalid JSON format')
    except KeyError:
        print('Invalid key')
    return meta


def fetch_datasource_uid() -> str:
    datasources = None
    url = host + f"/api/datasources"
    try:
        response = requests.get(url, headers=headers)
        datasources = response.json()

        # find name is data_source
        for source in datasources:
            if source['name'] == datasource_name:
                return source['uid']
    except json.JSONDecodeError:
        print('Invalid JSON format')
    except KeyError:
        print('Invalid key')
    return None


def update_default_query(sql: str, graph_type:str, start: str, end:str, config):
    # 1. Read version
    default_meta = fetch_dashboard(config.default_dashboard_uid)
    if default_meta is None or "meta" not in default_meta:
        return HttpResponseBadRequest(json.dumps({"message": "Get sql graph failed: not found default dashboard meta."}))
    version = default_meta['meta']['version']

    data = {
        "dashboard": {
            "annotations": {
                "list": [
                    {
                    "builtIn": 1,
                    "datasource": {
                        "type": "grafana",
                        "uid": "-- Grafana --"
                    },
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                    }
                ]
            },
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "id": config.default_dashboard_id,
            "links": [
                {
                    "asDropdown": True,
                    "icon": "external link",
                    "includeVars": True,
                    "keepTime": True,
                    "tags": [],
                    "targetBlank": True,
                    "title": "New link",
                    "tooltip": "",
                    "type": "dashboards",
                    "url": ""
                }
            ],
            "liveNow": True,
            "panels": [
                {
                    "datasource": {
                        "type": "influxdb",
                        "uid": config.datasource_uid
                    },
                    "targets": [{"query": sql}],
                    "title": "default",
                    "type": graph_type
                }
            ],
            "refresh": False,
            "schemaVersion": 38,
            "style": "dark",
            "tags": [],
            "templating": {
            "list": []
            },
            "time": {
                "from": start,
                "to": end
            },
            "timepicker": {},
            "timezone": "",
            "title": "default",
            "uid": config.default_dashboard_uid,
            "version": version,
            "weekStart": ""
        },
        "message": "",
        "overwrite": False,
        "folderUid": config.folder_uid
    }

    # add pie config
    if graph_type == "piechart":
        pie_config = {
            "datasource": {
                "type": "influxdb",
                "uid": config.datasource_uid
            },
            "targets": [{"query": sql}],
            "title": "default",
            "type": graph_type,
            "fieldConfig":{
                "defaults": {
                "color": {
                    "mode": "palette-classic"
                },
                "custom": {
                    "hideFrom": {
                    "legend": False,
                    "tooltip": False,
                    "viz": False
                    }
                },
                "mappings": []
                },
                "overrides": []
            },
            "gridPos": {
                "h": 10,
                "w": 8,
                "x": 0,
                "y": 0
            },
            "id": 1,
            "options": {
                "displayLabels": [
                    "percent"
                ],
                "legend": {
                "displayMode": "list",
                "placement": "right",
                "showLegend": True,
                "values": []
                },
                "pieType": "pie",
                "reduceOptions": {
                "calcs": [
                    "lastNotNull"
                ],
                "fields": "",
                "values": False
                },
                "tooltip": {
                "mode": "single",
                "sort": "none"
                }
            }
        }

        data["dashboard"]["panels"][0] = pie_config

    elif graph_type == "barchart":
        bar_config = {
            "datasource": {
                "type": "influxdb",
                "uid": config.datasource_uid
            },
            "targets": [{"query": sql}],
            "title": "default",
            "type": graph_type,
            "fieldConfig": {
                "defaults": {
                "color": {
                    "mode": "palette-classic"
                },
                "custom": {
                    "axisCenteredZero": False,
                    "axisColorMode": "text",
                    "axisLabel": "",
                    "axisPlacement": "auto",
                    "fillOpacity": 80,
                    "gradientMode": "none",
                    "hideFrom": {
                    "legend": False,
                    "tooltip": False,
                    "viz": False
                    },
                    "lineWidth": 1,
                    "scaleDistribution": {
                    "type": "linear"
                    },
                    "thresholdsStyle": {
                    "mode": "off"
                    }
                },
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                    {
                        "color": "green",
                        "value": None
                    },
                    {
                        "color": "red",
                        "value": 80
                    }
                    ]
                }
                },
                "overrides": []
            },
            "gridPos": {
                "h": 12,
                "w": 10,
                "x": 0,
                "y": 0
            },
            "id": 1,
            "options": {
                "barRadius": 0,
                "barWidth": 0.97,
                "fullHighlight": False,
                "groupWidth": 0.7,
                "legend": {
                "calcs": [],
                "displayMode": "list",
                "placement": "bottom",
                "showLegend": True
                },
                "orientation": "auto",
                "showValue": "auto",
                "stacking": "none",
                "tooltip": {
                "mode": "single",
                "sort": "none"
                },
                "xTickLabelRotation": 0,
                "xTickLabelSpacing": 0
            }
        }

        data["dashboard"]["panels"][0] = bar_config

    url = host + '/api/dashboards/db'
    try:
        response = requests.post(url, headers=headers, json=data)
        response = response.json()
        return response

    except json.JSONDecodeError:
        print('Invalid JSON format')
        return None
    except KeyError:
        print('Invalid key')
        return None

def get_user_folder(folder_name: str):
    url = host + f"/api/search?limit=1000&query={folder_name}"
    try:
        response = requests.get(url, headers=headers)
        results = response.json()
        if len(results) > 0:
            return results[0]
    except json.JSONDecodeError:
        print('Invalid JSON format')
    except KeyError:
        print('Invalid key')
    return None

def create_user_folder(folder_name: str):
    url = host + f"/api/folders"
    data = {
        "title": folder_name
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if result is not None:
            return result
    except json.JSONDecodeError:
        print('Invalid JSON format')
    except KeyError:
        print('Invalid key')
    return None

def create_dashboard(folder_uid: str, dashboard: str):
    print("folder uid:"+folder_uid)

    url = host + f"/api/dashboards/db"
    data = {
        "dashboard": {
            "id": None,
            "uid": None,
            "title": dashboard,
            "tags": [ "templated" ],
            "timezone": "browser",
            "schemaVersion": 38,
            "refresh": "25s"
        },
        "folderUid": folder_uid,
        "message": "create dashboard",
        "overwrite": False
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        results = response.json()

        if results is not None:
            return results
    except json.JSONDecodeError:
        print('Invalid JSON format')
    except KeyError:
        print('Invalid key')
    return None

def init_dashboards(user: User):
    """
    1. Create folder named 'user_x' for current user
    2. Create 'default' and 'custom' dashboards for current user
    """
    folder_name = f"user_{user.id}"
    # if don't have folder named 'user_x', just create it
    folder = get_user_folder(folder_name)
    print(245)
    print(folder)
    if folder is None or 'message' in folder:
        folder = create_user_folder(folder_name)
    if folder is None:
        return None
    
    print(252)
    print(folder)

    # if don't have 'default' and 'custom' dashboards, just create them
    default = None
    custom = None
    dashboards = fetch_dashboards()
    if dashboards is not None and len(dashboards) > 0:
        for item in dashboards:
            if item['title'] == 'default' and item['type'] == 'dash-db' and item['folderTitle'] == folder_name:
                default = item
            if item['title'] == 'custom' and item['type'] == 'dash-db' and item['folderTitle'] == folder_name:
                custom = item

    if default is None:
        default = create_dashboard(folder['uid'], 'default')
        if default is None:
            return None
    if custom is None:
        custom = create_dashboard(folder['uid'], 'custom')
        if custom is None:
            return None
    
    datasource_uid = fetch_datasource_uid()
    if datasource_uid is None:
        return HttpResponseBadRequest(json.dumps({"message": "Not found datasource uid."}))

    config = UserDashboard.objects.create(
        user=user,
        folder_uid=folder['uid'],
        custom_dashboard_id=custom['id'],
        custom_dashboard_uid=custom['uid'],
        default_dashboard_id=default['id'],
        default_dashboard_uid=default['uid'],
        datasource_uid=datasource_uid
    )
    return config

def get_dashboard_version(uid: str):
    default_meta = fetch_dashboard(uid)
    if default_meta is None or "meta" not in default_meta:
        return None
    return default_meta['meta']['version']

def create_custom_query(sql: str, title: str, start: str, end:str, config):
    # 1. Read version
    custom = fetch_dashboard(config.custom_dashboard_uid)
    if custom is None:
        return HttpResponseBadRequest(json.dumps({"message": "Get sql graph failed: not found custom dashboard meta."}))
    
    # 2. Read current panel num
    dashboard = custom['dashboard']
    print(dashboard)

    if 'panels' in dashboard:
        panels = dashboard['panels']
    else:
        panels = []
    panel_num = len(panels)
    panels.append({
        "datasource": {
            "type": "influxdb",
            "uid": config.datasource_uid
        },
        "targets": [{"query": sql}],
        "title": title,
        "type": "timeseries"
    })
    dashboard['panels'] = panels

    data = {
        "dashboard": dashboard,
        "message": "",
        "overwrite": False,
        "folderUid": config.folder_uid
    }
    url = host + '/api/dashboards/db'
    try:
        response = requests.post(url, headers=headers, json=data)
        return panel_num+1

    except json.JSONDecodeError:
        print('Invalid JSON format')
        return None
    except KeyError:
        print('Invalid key')
        return None


def remove_custom_query(dashboard_index: int, config):
    # 1. Read version
    custom = fetch_dashboard(config.custom_dashboard_uid)
    if custom is None:
        return None
    
    # 2. Read current panel num
    dashboard = custom['dashboard']
    print(dashboard)

    if 'panels' in dashboard:
        panels = dashboard['panels']
    else:
        return None
    del panels[dashboard_index-1]
    dashboard['panels'] = panels
    data = {
        "dashboard": dashboard,
        "message": "",
        "overwrite": False,
        "folderUid": config.folder_uid
    }
    url = host + '/api/dashboards/db'
    try:
        response = requests.post(url, headers=headers, json=data)
        return True

    except json.JSONDecodeError:
        print('Invalid JSON format')
        return None
    except KeyError:
        print('Invalid key')
        return None


