import {React, useState} from 'react'

const TeamView = (props) => {
    const [currTeam, setCurrTeam] = useState(props.location.state.team)
    return (
        <div>
            <ul>
                {
                    currTeam.map(player => {
                        <li>{player.player.name}</li>
                    })
                }
            </ul>
        </div>
    )
}

export default TeamView