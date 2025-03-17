import { Link, useNavigate } from 'react-router-dom'
import { register } from '@api/userAPI'
import { useState } from 'react'

function Register() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm_password, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const redirect = () => {
    navigate("/login", {replace: true})
  }

  const handleRegister = () => {
    setError('')
    register(username, password, redirect, setError)
  }

  const errorMsg = password != confirm_password ? <div className='text-red-500'>Password is different</div> : error == '' ? '' : <div className='text-red-500'>{error}</div>

  const disableRegister = password != confirm_password ? true : false

  return (
    <>
      <div className='flex flex-col justify-center items-center my-auto mx-auto h-screen w-fit space-y-4'>
        <h1>Register</h1>
        <div className='flex flex-col items-end space-y-2 '>
        <div className='flex space-x-2 items-center'>
          <label>Username(Email):</label>
          <input className='border border-gray-500 rounded-xl p-2 w-64' type='text' name='email' value={username} onChange={(e) => setUsername(e.target.value)} />
        </div>
        <div className='flex space-x-2 items-center'>
          <label>Password:</label>
          <input className='border border-gray-500 rounded-xl p-2 w-64' type='password' name='confirm_password' value={password} onChange={(e) => setPassword(e.target.value)}/>
        </div>
        <div className='flex space-x-2 items-center'>
          <label>Confirm Password:</label>
          <input className='border border-gray-500 rounded-xl p-2 w-64' type='password' name='confirm_password' value={confirm_password} onChange={(e) => setConfirmPassword(e.target.value)}/>
        </div>
        {errorMsg}
        </div>
        <button disabled={disableRegister} onClick={handleRegister}>Regiter</button>
        <Link to={`/login`}>Back to Login</Link>

      </div>
    </>
  )
}

export default Register
