// login ICY and 
/*urls = [
    'https://icardyou.icu/sendpostcard/myPostCard/2?status=&cardType=&nowPage=1',
    'https://icardyou.icu/sendpostcard/myPostCard/2?status=&cardType=&nowPage=2',
    'https://icardyou.icu/sendpostcard/myPostCard/2?status=&cardType=&nowPage=3',
    .................
]*/
// do it one by one

// received
var allData = [];
$('tr').each(function() {
    var tds = $(this).find('td');
    if (tds.length > 2 && tds.eq(2).text().trim() === "已收到") {
        var firstTdText = tds.eq(0).text().trim();
        var secondTdA = tds.eq(1).find('a');
        var secondTdAHref = secondTdA.attr('href');
        var secondTdAText = secondTdA.text().trim();
        var rowData = [firstTdText, secondTdAHref, secondTdAText];
        allData.push(rowData);
    }
});
console.log(JSON.stringify(allData));

//sent
var allData = [];
$('tr').each(function() {
    var tds = $(this).find('td');
    if (tds.length > 2 && (tds.eq(2).text().trim() === "已收到" || tds.eq(2).text().trim() === "已过期")) {
        var firstTdText = tds.eq(0).text().trim();
        var secondTdA = tds.eq(1).find('a');
        var secondTdAHref = secondTdA.attr('href');
        var secondTdAText = secondTdA.text().trim();
        var rowData = [firstTdText, secondTdAHref, secondTdAText];
        allData.push(rowData);
    }
});
console.log(JSON.stringify(allData));


//pc
// Function to extract table data and generate CSV
function extractTableDataToCSV() {
    // Select the table element
    const table = document.querySelector('#postcardTable');
    const rows = table.querySelectorAll('tbody tr');

    // Prepare CSV data
    const csvData = [];
    csvData.push([
        'no', 'id', 'title', 'type', 'platform', 'friend_id', 'country', 'region',
        'sent_date', 'received_date', 'tags', 'url', 'friend_url'
    ]);

    // Iterate through rows and extract data
    rows.forEach((row, index) => {
        const cells = row.querySelectorAll('td');
        const idCell = cells[0];
        const friendCell = cells[1];
        const countryCell = cells[2];
        const sentDateCell = cells[3];
        const receivedDateCell = cells[4];

        const id = idCell.textContent.trim();
        const url = idCell.querySelector('a') ? idCell.querySelector('a').href : '';
        const friendId = friendCell.textContent.trim();
        const friendUrl = friendCell.querySelector('a') ? friendCell.querySelector('a').href : '';
        const country = countryCell.textContent.trim();
        const sentDate = sentDateCell.textContent.trim();
        const receivedDate = receivedDateCell.textContent.trim();

        csvData.push([
            '', // no
            id, // id
            '', // title
            'MATCH', // type
            'POSTCROSSING', // platform
            friendId, // friend_id
            country, // country
            '', // region
            sentDate, // sent_date
            receivedDate, // received_date
            '', // tags
            url, // url
            friendUrl // friend_url
        ]);
    });

    // Convert CSV data to string
    const csvString = csvData.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

    // Create a downloadable CSV file
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'postcards.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// Run the function
extractTableDataToCSV();