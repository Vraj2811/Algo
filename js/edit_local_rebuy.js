let algotraderApi = "http://13.234.78.227:8080/get_rebuy_details"
window.addEventListener('load', () => {
    // get the name and exchange details from url
    const urlParams = (new URL(document.location)).searchParams;
    const name = urlParams.get('r_name');
    const exchange = urlParams.get('r_exchange');

    // call the algotrader api to get details.
    fetch(algotraderApi, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            r_name: name,
            r_exchange: exchange
        })
    }).then(res => {
        if (res.ok){
            return res.json()
        }
        else { 
            return {
                'message': 'Not able to connect to flask API',
                'status': 500,
                'data': {}

            }.json()
        }
    }).then(resp_data => {
        

        if (resp_data.status == 200){
            // autofill the textfields
            document.getElementById('base_price').value = resp_data.data.base_price;
            document.getElementById('update_rebuy_perc').value = resp_data.data.rebuy_perc;
            document.getElementById('update_rebuy_quant').value = resp_data.data.rebuy_quant;
            document.getElementById('update_exit_perc').value = resp_data.data.exit_perc;
            
        } 
        else {
            // print the error in red.
            document.getElementById('error').innerHTML = resp_data.message;

        }
        
    })
    // Autofil to the text fields
    document.getElementById('update_name').value = name;
    document.getElementById('update_exchange').value = exchange;
    
})