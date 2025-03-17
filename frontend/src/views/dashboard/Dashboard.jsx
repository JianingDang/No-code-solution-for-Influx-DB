import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../provider/authProvider';
import { logout } from '../../api/userAPI';
import { doQuery } from '../../api/influxdbAPI';
import { useState, useEffect } from 'react';

import { SelectListDom } from '@components/selectListDom';
import { SelectFieldDom } from '@components/selectFieldDom'
import { FilterFieldDom } from '@components/filterFieldDom'
import { TableDom } from '@components/tableDom';

import { DndProvider } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { flushSync } from 'react-dom';
import Tab from '../../components/tab';
import useBuckets from './BuckectsDom';
import useMeasurements from './measurementsDom';
import useFields from './fieldsDom';
import useGraph from './GraphDom';

import History from './History';

function Dashboard() {
    const [error, setError] = useState('')
    

    const [selectBucket, setSelectBucket ] = useState('')
    const [selectMeasurement, setSelectMeasurement ] = useState('')
    const [selectFields, setSelectFields ] = useState([])
    const [filterFields, setFilterFields ] = useState([])

    const [startTime, setStartTime] = useState(new Date())
    const [endTime, setEndTime] = useState(new Date())

    const [limit, setLimit] = useState('10')

    const {user, setToken} = useAuth()
    const navigate = useNavigate()
    const {BucketsDom, buckets} = useBuckets({
      bucket:selectBucket,
      setBucket: setSelectBucket
    })
    const {MeasurementsDom, measurements} = useMeasurements({
      bucket: selectBucket,
      measurement: selectMeasurement,
      setMeasurement: setSelectMeasurement
    })
    const { FieldsDom, fields } = useFields({
      bucket: selectBucket,
      measurement: selectMeasurement
    })
    const { 
      container: graphDom,
      setShareURL,
      fetchQuery: fetchGraph
    } = useGraph()

    const [tableData, setTableData] = useState([
      {
        "_measurement":"",
        "_field":"",
        "_value":"",
        "_start":"",
        "_stop":"",
        "_time":""
      }
    ])

    useEffect(() => {
      if (buckets.length > 0) {
        console.log("buckets updated, so update select bucket...")
        setSelectBucket(buckets[0]);
      }
    }, [buckets]);

    useEffect(() => {
      if (measurements.length > 0) {
        console.log("measurements updated, so update select bucket...")
        setSelectMeasurement(measurements[0]);
      }
    }, [measurements]);

    function handleQuery() {
      console.log("start query...")
      doQuery(sql, setTableData, setError)
      fetchGraph({
        sql, 
        _startTime: startTime,
        _endTime: endTime,
        _limit: limit,
        setError: setError
      })
    }

    function addSelect(field) {
      if (selectFields.findIndex((element) => element.name == field.name) > -1) {
        console.log("this field have exists.")
        return
      }

      let newSelctField = {
        bucket: field.bucket,
        measurement: field.measurement,
        data_type: field.data_type,
        name: field.name,
        alias: ''
      }
      // generate alias name
      let id = 0
      let alias = `field_${id}`

      while (selectFields.findIndex((element) => element.alias == alias) > -1) {

        id = id+1
        alias = `field_${id}`
      }

      newSelctField.alias = alias
      let current = [...selectFields, newSelctField]

      console.log("copy new field into select fields:", selectFields, current)
      flushSync(() => {
        setSelectFields(current)
      })
    }

    function addFilter(field) {
      // default filter is:
      // {combine_type} {name} {op} {right}, e.g: and xxx = ''
      let newFilterField = {
        combine_type: 'and',
        bucket: field.bucket,
        measurement: field.measurement,
        data_type: field.data_type,
        name: field.name,
        alias: '',
        op: '=',
        right: ''
      }
      // generate alias name
      let id = 0
      let alias = `field_${id}`

      while (filterFields.findIndex((element) => element.alias == alias) > -1) {
        id = id+1
        alias = `field_${id}`
      }

      newFilterField.alias = alias
      let current = [...filterFields, newFilterField]

      console.log("copy new field into filter fields:", filterFields, current)
      flushSync(() => {
        setFilterFields(current)
      })
    }

    function deleteFilter(alias) {
      const currentFilters = [...filterFields]
      const index = filterFields.findIndex((element) => element.alias == alias)
      if (index == -1) {
        return
      }
      console.log("try to delete filter field", alias)
      currentFilters.splice(index, 1)
      setFilterFields(currentFilters)
    }

    function updateFilter(newFilter) {
      const currentFilters = [...filterFields]
      const index = filterFields.findIndex((element) => element.alias == newFilter.alias)
      if (index == -1) {
        return
      }
      console.log("try to update filter field", newFilter)
      currentFilters[index] = newFilter
      setFilterFields(currentFilters)
    }

    const redirect = () => {
      navigate("/login", {replace: true})
    }

    const genSQL = (fields, filters) => {
      if (fields.length == 0) {
        return ''
      }

      // get target bucket
      const bucket = fields[0].bucket
      // get target measurement
      const measurement = fields[0].measurement

      // generate select measurements
      const selectFieldsStr = fields.reduce((result, field, index) => {
        if (index === 0) {
          return `r[\"_field\"] == \"${field.name}\"`
        } else {
          return result + ` or r[\"_field\"] == \"${field.name}\"`
        }
      }, "")

      console.log("start", startTime, "end", endTime)
      let timerange = ""
      if (new Date(endTime).toISOString() == new Date(startTime).toISOString()) {
        timerange = `start: ${new Date(startTime).toISOString()}`
      } else if (new Date(endTime) > new Date(startTime)) {
        timerange = `start: ${new Date(startTime).toISOString()}, stop: ${new Date(endTime).toISOString()}`
      } else {
        timerange = `start: ${new Date(endTime).toISOString()}, stop: ${new Date(startTime).toISOString()}`
      }

      // generate filters
      let filtersStr = ""
      if (filters.length > 0) {
        
        filtersStr = filters.reduce((result, filter_, index) => {
          if (filter_.right == '') {
            return result
          }

          let condition = `((r["_field"] == "${filter_.name}" and r["_value"] ${filter_.op} ${filter_.right}) or r["_field"] != "${filter_.name}")`
          if (index > 0) {
            condition = ` ${filter_.combine_type} ` + condition
          }
          return result + condition
        }, "")

        if (filtersStr != '') {
          filtersStr = `|> filter(fn: (r) => ${filtersStr})`
        }

      }

      const sql = `from(bucket: "${bucket}")
  |> range(${timerange})
  |> filter(fn: (r) => r["_measurement"] == "${measurement}")
  |> filter(fn: (r) => ${selectFieldsStr})
  ${filtersStr}
  |> limit(n: ${limit})`

      return sql
    }

    const sql = genSQL(selectFields, filterFields)

    const sqlTextare = <textarea className='w-full min-h-96 border border-gray-500 rounded-xl p-4' defaultValue={sql}></textarea>

    const dataTable = <TableDom data={tableData} sql={sql} />

    const tabData = [
      {title: "SQL", content: sqlTextare},
      {title: "Graph", content: graphDom},
      {title: "Table", content: dataTable},
      {title: "Saved List", content: <History />}
    ]

  return (
    <>
      <div className='flex flex-col mx-auto max-w-screen-xl items-start px-8'>

      <DndProvider backend={HTML5Backend}>
      <nav className='flex items-center pt-4 space-x-2'>
        <div>
            Current Login: {user.email}
        </div>
        <button onClick={() => {logout(setToken, redirect)}}>Logout</button>
      </nav>
      <h1 className='text-5xl py-4'>InfluxDB Viewer</h1>
      <div className='flex m-auto w-full justify-center'>

        <div className='max-w-96'>
          <div className='my-2'>
          Time Range:
          </div>
          <div className='flex space-x-2 items-center mb-2' >
              <h2 className='min-w-12'>From </h2>
              <input value={startTime} onChange={(e) => setStartTime(e.target.value)} className='border border-gray-500 rounded-xl p-2' type="datetime-local" />
          </div>
          <div className='flex space-x-2 items-center' >
              <h2 className='min-w-12'>To </h2>
              <input value={endTime} onChange={(e) => setEndTime(e.target.value)} className='border border-gray-500 rounded-xl p-2' type="datetime-local" />
          </div>
          <div className='flex justify-between mb-2'>
            
            <div className='flex flex-col justify-between w-full space-y-2'>
            <div className='flex justify-between w-full'>
              {BucketsDom}
            </div>
            <div className='flex justify-between w-full'>
              {MeasurementsDom}
            </div>
            <div className='w-full'>
              {FieldsDom}
            </div>
            <div className='w-full'>
              <h2 className='py-2'>Selected</h2>
                <SelectListDom handleDrop={addSelect} state={selectFields}>
                  {selectFields.map((field, index) => <SelectFieldDom key={`select-field-${index}`} field={field} />)}
                </SelectListDom>
            </div>
            <h2 className='py-2'>Get First n rows data: (Due to normal viewing data requirements, there is a limit of 500 entries)</h2>
            <div className='flex space-x-2 items-center w-full'>
              <select value={limit} onChange={(e) => setLimit(e.target.value)} className='w-full	border border-gray-200 rounded-xl p-2'>
                <option value="10">10</option>
                <option value="100">100</option>
                <option value="500">500</option>
              </select>
            </div>
            <button className='my-2' onClick={handleQuery}>Submit</button>
            </div>
          </div>
        </div>

        <div className='w-full'>
        <Tab data={tabData} />
        <div className='w-full ml-4'>
          <h2 className='py-2'>
              Filter
          </h2>
          <div className='py-4'>
          <SelectListDom handleDrop={addFilter} state={filterFields}>
            {filterFields.map((field, index) => <FilterFieldDom key={`filter-field-${index}`} field={field} deleteFilter={deleteFilter} updateFilter={updateFilter} />)}
          </SelectListDom>
          </div>
        </div>
        </div>

      </div>

      </DndProvider>

      </div>
    </>
  )
}

export default Dashboard
