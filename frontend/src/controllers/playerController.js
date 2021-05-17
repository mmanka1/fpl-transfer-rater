import axios from 'axios';

export const getPlayers = async() => {
    try {
        let res = await axios.get('http://localhost:5000/players')
        return res.data
    } catch(err) {
        console.log(err)
        return {
            error: true,
            message: err
        }
    }
}