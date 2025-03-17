import { useState, useEffect } from "react"

export const Select = ({title, options, value, changeValue}) => {

    return (<>
    <div className=''>
        <h2 className='py-2'>
            {title}:
        </h2>
        <select
            className="border p-2 rounded-md w-full"
            value={value}
            onChange={(e) => changeValue(e.target.value)}
        >
        {options.map((o, index) => 
            <option 
                className="w-full"
                key={`select-${title}-op-${index}`} 
                value={o}
            >
            {o}
            </option>
        )}
        </select>
    </div>
    </>)
}