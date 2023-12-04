const shareCardTemplate = document.querySelector('#share-card-template');
const shareCardContainer = document.querySelector('#share-card-container');
const searchInput = document.querySelector('#z_share_name');

let instruments = []
fetch("http://3.110.182.250:8080/get_instruments",{
    method: 'POST',
    headers: {'Content-Type': 'application/json'}
}).then(res => res.json()).then(data =>{
    var i = 0
    instruments = data.map(instrument => {
        var card = shareCardTemplate.content.cloneNode(true).children[0];
        card.id =i
        i = i+1
        //console.log(card, card.className, card.id)
        const header = card.querySelector('#card-header')
        const body = card.querySelector('#card-body')
        const body2 = card.querySelector('#card-body-2')
        header.textContent = instrument.tradingsymbol
        body.textContent = instrument.exchange
        body2.textContent = instrument.instrument_token
        
        shareCardContainer.append(card)
        return {share: instrument.tradingsymbol, exchange: instrument.exchange, token: instrument.instrument_token, element: card}  
    })
    
})

// serch functionality
searchInput.addEventListener("input", (e) => {
    const value = e.target.value.toLowerCase()
    // loop over each instrument and check if it should be visible
    instruments.forEach(instrument => {
        const isVisible = instrument.share.toLowerCase().startsWith(value)
        if (isVisible && value) {
            instrument.element.style.display = "block"
        }
        else {
            instrument.element.style.display = "none"
        }
    })
})

// event listner for card elements
document.addEventListener('click', e =>{
    const target_parent_elem = e.target.parentElement
    if (e.target && target_parent_elem.className == 'card')
    {
        // get the card
        card = document.getElementById(target_parent_elem.id)
        const header = card.querySelector('#card-header').textContent
        const body = card.querySelector('#card-body').textContent
        const body2 = card.querySelector('#card-body-2').textContent
        // console.log(header, body)

        // set the inputs of the form accordingly
        document.getElementById("z_share_name").value = header
        document.getElementById("z_exchange").value = body
        document.getElementById("token").value = body2
    }
})