import { downloadExcel } from "../api/influxdbAPI"

export const TableDom = ({data, sql}) => {
  const cols = [
    "_measurement","_field","_value","_start","_stop","_time",
  ]
  return (
    <>
    <div className="p-0 m-0 rounded-xl">

      <button onClick={() => downloadExcel(sql)}>
        Download Excel
      </button>

      <table className="">
        <thead>
            {cols.map((col, i) => <th className="rounded-t-xl border border-gray-500 p-2" key={`col-${i}`}>{col}</th>)}
        </thead>
        <tbody>
            {data.map((row, rowi) => {
              return <tr key={`row-${rowi}`}>
                {cols.map((col,coli) => <td className="border border-gray-500 p-2" key={`row-${rowi}-${coli}`}>{row[col]}</td>)}
                </tr>
            })}
        </tbody>
      </table>
    </div>
    </>
  )
}