import axios from 'axios';

export const getTeam = async(userId) => {
    try {
        let res = await axios.get('http://localhost:5000/myteam', {
            params: {
                id: userId
            }
        })
        return res.data
        
    } catch(err) {
        console.log(err)
        return {
            error: true,
            message: err
        }
    }
}