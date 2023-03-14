
const { config } = require('dotenv');
const config_controller = require('./configuration');

exports.decode_communication_protocol = async (dec_message) => {
    
    var data = JSON.parse(dec_message);

    switch (data.method) {
        case 'Config': 
            if (data.type === 'POST') {
                return await config_controller.set_up_configuration(data.data);
            }
        break;

        default: break;
    }
}

exports.dispose = () => {
    config_controller.dispose();
}