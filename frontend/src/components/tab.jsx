import { useState } from "react";
function Tab({data}) {
  const [active, setActive] = useState(data[0].title);

  const display = data.filter((t) => t.title === active).length > 0 ? data.filter((t) => t.title === active)[0].content : ''

  return (<>
        <div className="flex flex-col w-full ml-4">
            <div className="flex">
            {data.map((type, index) => (
                <div
                key={`tab-${index}`}
                className={(active === type.title ? '  text-sky-500 border-b-2 border-b-sky-500' : '  text-black ') + ' py-2 px-4'}
                onClick={() => setActive(type.title)}
                >
                {type.title}
                </div>
            ))}
            </div>
            <div className=" py-4 ">
                {display}
            </div>
        </div>
      </>);
}

export default Tab;