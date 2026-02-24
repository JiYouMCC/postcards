// Postcrossing Expired Postcard Scraper
// Run this in browser console on a Postcrossing travelingpostcard page
// For example: https://www.postcrossing.com/travelingpostcard/CN-4195967

function extractExpiredPostcardData() {
    // Get postcard ID from URL or page title
    const urlMatch = window.location.pathname.match(/travelingpostcard\/([A-Z]{2}-\d+)/);
    const titleMatch = document.title.match(/Postcard ([A-Z]{2}-\d+)/);
    const postcardId = urlMatch ? urlMatch[1] : (titleMatch ? titleMatch[1] : '');
    
    if (!postcardId) {
        console.error('Cannot find postcard ID');
        return null;
    }

    // Get friend info (receiver)
    let friendId = '';
    let friendUrl = '';
    const friendLink = document.querySelector('.user-details .name-username a[href^="/user/"]');
    if (friendLink) {
        friendId = friendLink.textContent.trim();
        friendUrl = 'https://www.postcrossing.com' + friendLink.getAttribute('href');
    }

    // Get country
    let country = '';
    let region = '';
    const countryLink = document.querySelector('.user-details .dashed-list a[href^="/country/"]');
    if (countryLink) {
        country = countryLink.textContent.trim();
        // Extract country name without flag emoji
        country = country.replace(/\s*[\u{1F1E6}-\u{1F1FF}]{2}\s*/gu, '').trim();
        
        // Get region from country link's title attribute (contains "State, Country" format)
        const countryTitle = countryLink.getAttribute('title');
        if (countryTitle) {
            region = countryTitle.split(',')[0].trim();
        }
    }

    // Handle Taiwan -> China mapping
    if (country === 'Taiwan') {
        country = 'China';
        region = '台湾';
    }

    // Get sent date
    let sentDate = '';
    const sentDateSpan = document.querySelector('.postcard-title .icons li:first-child span');
    if (sentDateSpan) {
        const dateText = sentDateSpan.textContent.trim();
        // Parse date like "23 Dec, 2025"
        const parsedDate = new Date(dateText);
        if (!isNaN(parsedDate)) {
            // Format as "YYYY-MM-DD HH:MM:SS +0000" (assuming UTC)
            const year = parsedDate.getFullYear();
            const month = String(parsedDate.getMonth() + 1).padStart(2, '0');
            const day = String(parsedDate.getDate()).padStart(2, '0');
            sentDate = `${year}-${month}-${day} 00:00:00 +0000`;
        }
    }

    // Received date is empty for expired postcards
    const receivedDate = '';

    // Postcard URL
    //const postcardUrl = `https://www.postcrossing.com/postcards/${postcardId}`;

    // Build result object
    const result = {
        no: '',
        id: postcardId,
        title: '',
        type: 'MATCH',
        platform: 'POSTCROSSING',
        friend_id: friendId,
        country: country,
        region: region,
        sent_date: sentDate,
        received_date: receivedDate,
        tags: '',
        url: '',
        friend_url: friendUrl
    };

    return result;
}

// Run extraction and output
const data = extractExpiredPostcardData();
if (data) {
    console.log('='.repeat(80));
    console.log('Extracted Postcard Data:');
    console.log('='.repeat(80));
    
    // Print CSV header
    console.log('no,id,title,type,platform,friend_id,country,region,sent_date,received_date,tags,url,friend_url');
    
    // Print CSV row
    const csvRow = [
        data.no,
        data.id,
        data.title,
        data.type,
        data.platform,
        data.friend_id,
        data.country,
        data.region,
        data.sent_date,
        data.received_date,
        data.tags,
        data.url,
        data.friend_url
    ].map(field => `"${field}"`).join(',');
    
    console.log(csvRow);
    
    console.log('='.repeat(80));
    console.log('JSON Format:');
    console.log(JSON.stringify(data, null, 2));
    console.log('='.repeat(80));
}
