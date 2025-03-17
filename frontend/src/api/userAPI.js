import axios from "axios";
import { flushSync } from 'react-dom';

const login = (username, password, setToken, setUser, redirect, setError) => {
    
    console.log("start loging: ", username, password)

    axios.post("/api/token/pair", {
        username: username,
        password: password
    })
    .then((result) => {
        const data = result.data
        flushSync(() => {
            setToken(data.access)
        })
        console.log("login result:", result, data.access)
        axios.get("/api/user/info")
            .then((result) => {
                console.log("get user info:", result.data)
                flushSync(() => {
                    setUser(result.data)
                })
                redirect()
            })
            .catch((e) => {
                setToken()
                console.error("get user info error:", e);
                if (e?.response?.data != undefined) {
                    console.error(e.response.data.detail)
                    if (e.response.status >= 300 && e.response.data.detail != undefined)
                        setError(e.response.data.detail)
                }
            })
    })
    .catch((e) => {
        console.error("login error:", e);
        if (e?.response?.data != undefined) {
            console.error(e.response.data.detail)
            if (e.response.status === 401 && e.response.data.detail != undefined)
                setError(e.response.data.detail)
        }
    })
}

const logout = (setToken, redirect) => {
    setToken()
    redirect()
}

const register = (username, password, redirect, setError) => {
    
    console.log("start register: ", username, password)

    axios.post("/api/user/register", {
        username: username,
        password: password
    })
    .then((result) => {
        console.log("register result:", result)
        redirect()
    })
    .catch((e) => {
        console.error("register error:", e);
        if (e?.response?.data != undefined) {
            console.error(e.response.data.message)
            if (e.response.status === 403 && e.response.data.message != undefined)
                setError(e.response.data.message)
        }
    })
}

export {login, logout, register}