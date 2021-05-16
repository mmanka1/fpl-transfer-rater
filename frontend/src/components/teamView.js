import {React, useState} from 'react'
import {useLocation} from 'react-router-dom';

const TeamView = (props) => {
    const location = useLocation()
    const [currTeam, setCurrTeam] = useState(location.state.team)
    const [currBank, setCurrBank] = useState(location.state.bank)
    console.log(currTeam)
    return (
        <div>
            <ul>
                {
                    currTeam.map(player => {
                        return <li>{player.player.name}</li>
                    })
                }
            </ul>
        </div>
    )
}

export default TeamView