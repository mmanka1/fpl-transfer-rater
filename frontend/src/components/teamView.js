import {React, useState, useEffect} from 'react';
import {useLocation} from 'react-router-dom';
import {ListGroup, Container, Row, Col, Card, Dropdown} from 'react-bootstrap';
import {getPlayers} from '../controllers/playerController';
import SelectSearch, {fuzzySearch} from 'react-select-search';

const TeamView = (props) => {
    const location = useLocation()
    const [currTeam, setCurrTeam] = useState(location.state.userData.team)
    const [currBank, setCurrBank] = useState(location.state.userData.bank)
    const [players, setPlayers] = useState([])
    const [error, setError] = useState('')

    useEffect(() => {
        getPlayers()
        .then(res => {
            if (res.error == true){
                setError(res.message)
            } else {
                setPlayers(res.message)
            }
        })
        .catch(err => {
            setError(err)
        })
    }, [])
    console.log("hi")
    console.log(players)
    return (
        <div>
            <Container>
                <Row>
                    <Col sm={4}>
                        <ListGroup variant="flush">
                            {
                                currTeam.map(player => {
                                    return (
                                            <ListGroup.Item>{player.player.name}</ListGroup.Item>
                                        )
                                })
                            }
                        </ListGroup>
                    </Col>
                    <Col sm={4}>
                        <h5>Bank: {currBank}</h5>
                    </Col>
                    <Col>
                        <SelectSearch 
                            options={players} 
                            search
                            filterOptions={fuzzySearch}
                            placeholder="Search for player" />
                    </Col>

                </Row>
            </Container>
        </div>
    )
}

export default TeamView