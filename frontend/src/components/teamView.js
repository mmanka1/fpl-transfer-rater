import {React, useState} from 'react';
import {useLocation} from 'react-router-dom';
import {ListGroup, Container, Row, Col, Card} from 'react-bootstrap'

const TeamView = (props) => {
    const location = useLocation()
    const [currTeam, setCurrTeam] = useState(location.state.userData.team)
    const [currBank, setCurrBank] = useState(location.state.userData.bank)
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
                </Row>
            </Container>
        </div>
    )
}

export default TeamView