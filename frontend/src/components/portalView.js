import {React, useState} from 'react';
import {Redirect} from 'react-router-dom';
import {getTeam} from '../controllers/userController';

const PortalView = () => {
    const [id, setId] = useState('')
    const [team, setTeam] = useState('')
    const [bank, setBank] = useState('')
    const [error, setError] = useState('')

    const handleChange = (event) => {
        setId(event.target.value)
    }

    const handleSubmit = (event) => {
        if (event != undefined) {
            event.preventDefault();
            getTeam(id)
            .then(res=>{
                if (res.error == true){
                    setError(res.message)
                } else {
                    setTeam(res.message.team)
                    setBank(res.message.bank)
                }
            })
            .catch(err => {
                setError(err)
            })
        }
    };

    return (
        <>
        {
            team != '' ? (
                <Redirect to = {{
                    pathname: "/team",
                    state: {
                        team: team,
                        bank: bank
                    }
                }}/>
            ) : (
                <div>
                    <form onSubmit ={handleSubmit}>
                    <h3>Find my team</h3>
                        <input type = "text" name = "id" placeholder = "Enter id" onChange={handleChange}/>
                        <input type = "submit" value ="Get Team"/>
                    </form>  
                    <div>
                    {
                        error != '' ? (
                            <div>
                                <h4>{error}</h4>
                            </div>
                        ) : <></>
                    }
                    </div>
                </div>
            )
        }
        </>
    )
}

export default PortalView