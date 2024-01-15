const shareCardTemplate = document.querySelector('#share-card-template');
const shareCardContainer = document.querySelector('#share-card-container');
const searchInput = document.querySelector('#z_share_name');

let users = []
fetch("http://123.123.123.123:8080/get_zerodha_holdings").then(res => res.json()).then(data =>{
    var i = 0
    users = data.map(user => {
        var card = shareCardTemplate.content.cloneNode(true).children[0];
        card.id =i
        i = i+1
        //console.log(card, card.className, card.id)
        const header = card.querySelector('#card-header')
        const body = card.querySelector('#card-body')
        header.textContent = user.tradingsymbol
        body.textContent = user.exchange
        
        shareCardContainer.append(card)
        return {share: user.tradingsymbol, exchange: user.exchange, element: card}  
    })
    
})

// serch functionality
searchInput.addEventListener("input", (e) => {
    const value = e.target.value.toLowerCase()
    // loop over each user and check if it should be visible
    users.forEach(user => {
        const isVisible = user.share.toLowerCase().includes(value)
        if (isVisible && value) {
            user.element.style.display = "block"
        }
        else {
            user.element.style.display = "none"
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
        console.log(header, body)

        // set the inputs of the form accordingly
        document.getElementById("z_share_name").value = header
        document.getElementById("z_exchange").value = body
    }
})