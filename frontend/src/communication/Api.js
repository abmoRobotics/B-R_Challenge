import axios from 'axios';
import config from './config.json';

export const getter = async (url) => {
    let result = await axios.get(config.server + url);
    return result.data;
};

export const setter = async (url, data) => {
    try {
        let result = await axios.post(config.server + url, data);
        return result.data;
    } catch (err) {
        console.log(err.message);
        return { error: true, data: { status: err?.response?.status, message: err?.response?.data?.message} }
    }
};

export const deleter = async (url) => {
    let result = await axios.delete(config.server + url);
    return result.data;
};