let algotraderApi = "http://3.110.182.250:8080/get_holding_details"
window.addEventListener('load', () => {
    // get the name and exchange details from url
    const urlParams = (new URL(document.location)).searchParams;
    const name = urlParams.get('z_share_name');
    const exchange = urlParams.get('z_exchange');

    // call the algotrader api to get details.
    fetch(algotraderApi, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            e_name: name,
            e_exchange: exchange
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
            document.getElementById('update_anbp').value = resp_data.data.anbp;
            document.getElementById('update_anbqp').value = resp_data.data.anbqp;
            console.log(resp_data.data.anbqp);
            document.getElementById('update_bsl').value = resp_data.data.bsl;
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