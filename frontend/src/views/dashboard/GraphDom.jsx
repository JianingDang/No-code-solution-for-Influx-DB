import { useState, useEffect } from "react";
import { createGraph, queryGraph, fetchGraphs } from "@api/influxdbAPI";

function useGraph() {
    const [startTime, setStartTime] = useState(new Date())
    const [endTime, setEndTime] = useState(new Date())
    const [SQLLimit, setSQLLimit] = useState(-1)
    const [graphType, setGraphType] = useState("timeseries")
    const [limit, setLimit] = useState(-1)
    const [query, setQuery] = useState('')
    const [title, setTitle] = useState('New Graph '+new Date())
    const [shareURL, setShareURL] = useState("")


    const fetchQuery = ({sql, _startTime, _endTime, _limit, setError}) => {
        setShareURL("")
        queryGraph(sql, graphType, setShareURL, setError)
        setQuery(sql)
        setStartTime(_startTime)
        setEndTime(_endTime)
        setSQLLimit(_limit)
    }

    useEffect(() => {
        var iframe = document.getElementById('iframe-graph');
        if (iframe != undefined) {
            iframe.contentWindow.location.reload();
        }
    }, [shareURL]);

    const setError = () => {}

    const saveGraph = () => {
        const graph = {
            title: title,
            query: query,
            range_start: startTime,
            range_end: endTime,
            limit: limit
        }
        console.log("saving current graph...", graph)
        createGraph(graph, setError)
    }

    const container = <>
        {shareURL == "" ? '':
        <div>
            <div className="flex items-center space-x-2 justify-between mb-2">
                <div className="flex items-center space-x-2">
                    <label htmlFor="graph-type">Graph Type</label>
                    <select className="border border-gray-500 rounded-xl p-2" name="graph-type" id="graph-type" value={graphType} onChange={(e) => setGraphType(e.target.value)}>
                        <option value="timeseries">Line Chart</option>
                        <option value="barchart">Bar Chart</option>
                        <option value="piechart">Pie Chart</option>
                    </select>
                </div>
                <button className="mb-2" onClick={() => fetchQuery({
                    sql: query,
                    _startTime: startTime,
                    _endTime: endTime,
                    _limit: SQLLimit,
                    setError: setError
                })}>Save</button>
            </div>

            <div className="flex items-center space-x-2 justify-between mb-2">
                <div className="flex items-center space-x-2">
                    <label htmlFor="new-graph-title">Title: </label>
                    <input className="w-96 border border-gray-500 rounded-xl p-2 "  id="new-graph-title" type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
                </div>
                <div className="flex items-center space-x-2">
                    <label htmlFor="graph-limit">Limit</label>
                    <select className="border border-gray-500 rounded-xl p-2" name="graph-Limit" id="graph-limit" value={(e) => setLimit(e.target.value)}>
                        <option value="-1">-1(No Limit)</option>
                        <option value={SQLLimit}>{SQLLimit}(The same as SQL)</option>
                    </select>
                </div>
                <button className="mb-2" onClick={() => saveGraph()}>Save</button>
            </div>
            <iframe id="iframe-graph" className="w-full h-full min-h-96" src={shareURL}></iframe>
        </div>
        }
    </>

    return {
        container, setShareURL, fetchQuery
    };
}

export default useGraph;