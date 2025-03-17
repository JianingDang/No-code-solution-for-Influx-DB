import { Link } from 'react-router-dom'
import { login } from '@api/userAPI'
import { useState } from 'react'
import { useAuth } from "../provider/authProvider";

function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const {setToken, setUser} = useAuth()

  const redirect = () => {
    console.log("redirecting to home page...")
    window.location.href = "/"
  }

  const handleLogin = () => {
    setError('')
    login(username, password, setToken, setUser, redirect, setError)
  }

  const errorMsg = error == '' ? '' : <div className='text-red-500'>{error}</div>


  return (
    <>
      <div className='flex flex-col justify-center items-center my-auto mx-auto h-screen w-fit space-y-4'>
      <h1>Login</h1>
      <div className='flex flex-col items-end space-y-2 '>
        <div className='flex space-x-2 items-center'>
          <label>Username(Email):</label>
          <input className='border border-gray-500 rounded-xl p-2 w-64' type='text' name='email' value={username} onChange={(e) => setUsername(e.target.value)}/>
        </div>
        <div className='flex space-x-2 items-center'>
          <label>Password:</label>
          <input className='border border-gray-500 rounded-xl p-2 w-64' type='password' name='password' value={password} onChange={(e) => setPassword(e.target.value)}/>
        </div>
        {errorMsg}
      </div>
      <button onClick={handleLogin}>Login</button>
      <Link to={`/register`}>Register a new account</Link>
      </div>
    </>
  )
}

export default Login
