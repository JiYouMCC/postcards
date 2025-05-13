// login ICY and 
/*urls = [
    'https://icardyou.icu/sendpostcard/myPostCard/2?status=&cardType=&nowPage=1',
    'https://icardyou.icu/sendpostcard/myPostCard/2?status=&cardType=&nowPage=2',
    'https://icardyou.icu/sendpostcard/myPostCard/2?status=&cardType=&nowPage=3',
    .................
]*/
// do it one by one
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
