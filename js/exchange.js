// ------- 工具类函数 -------

function Debounce(func, wait) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

const ExchangeManager = {
  _receivedData: undefined,
  _sentData: undefined,
  _userAliases: undefined,
  _currentSearchText: undefined,
  _currentFriendUrls: [],
  _filteredReceivedData: [],
  _filteredSentData: [],
  _baseUrl: "/postcards/",
  
  Init: function(receivedData, sentData, userAliasesData) {
    // 初始化数据
    ExchangeManager._receivedData = receivedData.sort((a, b) => new Date(b['received_date']) - new Date(a['received_date']));
    ExchangeManager._sentData = sentData.sort((a, b) => new Date(b['received_date']) - new Date(a['received_date']));
    ExchangeManager._userAliases = userAliasesData?.users || [];
    
    // 处理 tags
    ExchangeManager._receivedData.forEach(item => {
      item['tags'] = item['tags'] ? item['tags'].split(' ') : [];
      item['_source'] = 'received';
    });
    ExchangeManager._sentData.forEach(item => {
      item['tags'] = item['tags'] ? item['tags'].split(' ') : [];
      item['_source'] = 'sent';
    });
    
    ExchangeManager.InitUserSearch();
    ExchangeManager.ApplyFiltersFromUrl();

    // 获取好友列表并填充 datalist
    const friendSet = new Set();
    ExchangeManager._receivedData.forEach(item => {
      if (item['friend_id']) {
        friendSet.add(item['friend_id']);
      }
    });
    ExchangeManager._sentData.forEach(item => {
      if (item['friend_id']) {
        friendSet.add(item['friend_id']);
      }
    });

    const friendList = Array.from(friendSet).sort();
    const datalist = $('#datalistFriend');
    datalist.empty();
    datalist.append(friendList.map(friend => `<option value="${friend}">`));
  },
  
  // ------ 用户搜索相关 ------
  InitUserSearch: function() {
    const inputSearch = $('#inputFriendSearch');
    
    inputSearch.on('input', Debounce(() => {
      const searchText = inputSearch.val().trim();
      if (searchText.length === 0) {
        ExchangeManager.ClearSelection();
        return;
      }
      
      ExchangeManager.SearchAndDisplay(searchText);
    }, 300));

    const resetButton = $('#resetSearch');
    resetButton.on('click', () => {
      inputSearch.val('');
      ExchangeManager.ClearSelection();
    });
  },
  
  SearchAndDisplay: function(searchText) {
    const allData = [...ExchangeManager._receivedData, ...ExchangeManager._sentData];
    
    // 先检查是否有用户别名映射
    let targetUrls = [];
    let canonicalName = null;
    let allAliases = [];
    let matchedCards = [];
    
    // 查找别名配置
    const aliasEntry = ExchangeManager._userAliases.find(user => 
      user.search_aliases && user.search_aliases.some(alias => 
        alias.includes(searchText)
      )
    );
    
    if (aliasEntry) {
      // 找到别名配置，使用配置的 friend_urls
      canonicalName = aliasEntry.canonical_name;
      allAliases = aliasEntry.search_aliases || [];
      targetUrls = aliasEntry.friend_urls || [];
      
      // 通过 friend_urls 精确匹配
      matchedCards = allData.filter(item => 
        item['friend_url'] && targetUrls.includes(item['friend_url'])
      );
    } else {
      // 没有找到别名配置，使用原有的昵称搜索
      matchedCards = allData.filter(item => 
        item['friend_id'] && item['friend_id'].includes(searchText)
      );
    }
    
    if (matchedCards.length === 0) {
      $('#userStats').text('未找到匹配的用户');
      $('#statsAlert').hide();
      ExchangeManager.ClearSelection();
      return;
    }
    
    // 统计所有匹配的 friend_url 和昵称
    const friendUrls = new Set(matchedCards.map(card => card['friend_url']).filter(url => url));
    const nicknames = new Set(matchedCards.map(card => card['friend_id']).filter(id => id));
    
    // 统计收发数量
    const receivedCount = matchedCards.filter(card => card['_source'] === 'received').length;
    const sentCount = matchedCards.filter(card => card['_source'] === 'sent').length;
    
    // 更新统计信息
    let statsText = '';
    if (canonicalName) {
      // 使用别名系统
      statsText = `${canonicalName}`;
      if (allAliases.length > 1) {
        const otherAliases = allAliases.filter(a => a !== canonicalName).slice(0, 2);
        if (otherAliases.length > 0) {
          statsText += ` (${otherAliases.join(', ')}${allAliases.length > 3 ? '...' : ''})`;
        }
      }
      if (aliasEntry.notes) {
        statsText += ` - ${aliasEntry.notes}`;
      }
    } else {
      const nicknameText = Array.from(nicknames).join(', ');
      /*if (nicknameText.length > 200) {
        statsText = `${nicknameText.slice(0, 200)}...`;
      } else {*/
        statsText = `${nicknameText}`;
      /*}*/
      const urlCount = friendUrls.size;
      
      if (urlCount > 1) {
        statsText += ` (${urlCount})`;
      }
    }
    $('#userStats').text(statsText);

    // 保存当前搜索文本
    ExchangeManager._currentSearchText = searchText;
    ExchangeManager._currentFriendUrls = Array.from(friendUrls);
    ExchangeManager._filteredReceivedData = matchedCards.filter(card => card['_source'] === 'received');
    ExchangeManager._filteredSentData = matchedCards.filter(card => card['_source'] === 'sent');
    
    // 显示统计和数据
    $('#receivedCount').text(ExchangeManager._filteredReceivedData.length);
    $('#sentCount').text(ExchangeManager._filteredSentData.length);
    $('#statsAlert').show();
    
    ExchangeManager.RefreshContainers();
    ExchangeManager.UpdateUrlParameters();
  },
  
  ClearSelection: function() {
    ExchangeManager._currentSearchText = undefined;
    ExchangeManager._currentFriendUrls = [];
    ExchangeManager._filteredReceivedData = [];
    ExchangeManager._filteredSentData = [];
    $('#userStats').text('');
    $('#receivedCount').text('0');
    $('#sentCount').text('0');
    $('#statsAlert').hide();
    $('#receivedContainer').empty();
    $('#sentContainer').empty();
  },
  
  RefreshContainers: function() {
    ExchangeManager.GenerateImageContainer('#receivedContainer', ExchangeManager._filteredReceivedData, 'received');
    ExchangeManager.GenerateImageContainer('#sentContainer', ExchangeManager._filteredSentData, 'sent');
  },
  
  GenerateImageContainer: function(containerSelector, data, folder) {
    try {
      $('[data-bs-toggle="popover"]').popover('hide');
    } catch (e) {}
    
    $(containerSelector).empty();
    data.forEach(dataItem => {
      $(containerSelector).append(
        $("<div></div>")
          .attr("id", `image_${folder}_${dataItem['id']}`)
          .addClass("col-lg-4 col-md-6 mb-2 col-6 image-item px-1")
          .append(
            $("<img></img>")
              .addClass("img-fluid img-thumbnail postcard")
              .attr("src", `${ExchangeManager._baseUrl}${folder}/${dataItem['id']}.jpg`)
              .attr("alt", dataItem['id'])
              .attr("title", dataItem['id'])
              .attr("data-bs-toggle", "popover")
              .attr("data-bs-placement", "bottom")
              .attr("data-card-id", dataItem['id'])
              .attr("data-card-url", dataItem["url"])
              .attr("data-card-title", dataItem["title"])
              .attr("data-card-platform", dataItem["platform"])
              .attr("data-card-friend_id", dataItem["friend_id"])
              .attr("data-card-friend_url", dataItem["friend_url"])
              .attr("data-card-country", dataItem["country"])
              .attr("data-card-region", dataItem["region"])
              .attr("data-card-sent_date", dataItem["sent_date"])
              .attr("data-card-received_date", dataItem["received_date"])
              .attr("data-card-type", dataItem["type"])
              .attr("data-card-tags", dataItem["tags"])
          )
      );
    });
    
    // 添加 onerror 事件
    document.querySelectorAll('img').forEach(img => {
      img.onerror = function() {
        this.src = ExchangeManager._baseUrl + '/postcard.svg';
      };
    });
    
    ExchangeManager.RefreshPopoverListeners();
  },
  
  RefreshPopoverListeners: function() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
      popoverTriggerEl.addEventListener('shown.bs.popover', function() {
        ExchangeManager._Localize();
      });
      return new bootstrap.Popover(popoverTriggerEl);
    });
    popoverList.forEach(function(popover) {
      popover.dispose();
    });
    
    const myDefaultAllowList = bootstrap.Tooltip.Default.allowList;
    myDefaultAllowList.strong = ['data-localize'];
    myDefaultAllowList.a = ['data-localize', 'style', 'href', 'target', 'title', 'class'];
    myDefaultAllowList.span = ['data-localize', 'style', 'class'];
    
    const newpopoverList = popoverTriggerList.map(function(popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl, {
        html: true,
        allowList: myDefaultAllowList,
        content: function() {
          const cardID = popoverTriggerEl.getAttribute('data-card-id');
          const cardTitle = popoverTriggerEl.getAttribute('data-card-title') || cardID;
          const cardUrl = popoverTriggerEl.getAttribute('data-card-url') || "#";
          const cardType = popoverTriggerEl.getAttribute('data-card-type') || "";
          const friendId = popoverTriggerEl.getAttribute('data-card-friend_id') || "";
          const friendUrl = popoverTriggerEl.getAttribute('data-card-friend_url') || "#";
          const country = popoverTriggerEl.getAttribute('data-card-country') || "";
          const region = popoverTriggerEl.getAttribute('data-card-region') || "";
          const sentDate = new Date(popoverTriggerEl.getAttribute('data-card-sent_date'));
          let receivedDate = null;
          if (popoverTriggerEl.getAttribute('data-card-received_date')) {
            receivedDate = new Date(popoverTriggerEl.getAttribute('data-card-received_date'));
          }
          const tags = popoverTriggerEl.getAttribute('data-card-tags') || "";
          const platform = popoverTriggerEl.getAttribute('data-card-platform');
          let days = null;
          let receivedDataStr = null;
          if (receivedDate) {
            days = Math.floor((receivedDate - sentDate) / (1000 * 60 * 60 * 24));
            receivedDataStr = `${receivedDate.getFullYear()}-${receivedDate.getMonth() + 1}-${receivedDate.getDate()}`;
          }
          const sentDataStr = `${sentDate.getFullYear()}-${sentDate.getMonth() + 1}-${sentDate.getDate()}`;
          const location = region ? `<span data-localize="${country}">${country}</span> - <span data-localize="${region}">${region}</span>` : `<span data-localize="${country}">${country}</span>`;
          
          let resultHtml = `<a href="${cardUrl}" target="_blank" title="${cardUrl}"><strong>${cardTitle}</strong></a>`;
          resultHtml += `<br><strong data-localize="Username">Username</strong>: <a href="${friendUrl}" target="_blank" class="text-decoration-none" style="cursor: pointer;" title="${friendUrl}">${friendId}</a>`;
          resultHtml += `<br><strong data-localize="Location">Location</strong>: ${location}`;
          resultHtml += `<br><strong data-localize="Platform">Platform</strong>: ${platform}`;
          resultHtml += `<br><strong data-localize="Type">Type</strong>: <span data-localize="${cardType}">${cardType}</span>`;
          resultHtml += `<br>${sentDataStr} ~ `;
          if (receivedDate) {
            resultHtml += ` ${receivedDataStr} (${days} <span data-localize="day(s)">day(s)</span>)<br>`;
          } else {
            resultHtml += ` <span data-localize="Expired">Expired</span><br>`;
          }
          tags.split(',').forEach(tag => {
            if (tag) resultHtml += `<span class="me-1 badge text-bg-primary">${tag}</span>`;
          });
          return resultHtml;
        }
      })
    });
  },
  
  _Localize: function() {
    let language_code = "en";
    if (Cookies.get("local_language_code")) {
      language_code = Cookies.get("local_language_code");
    }
    localize.localize(language_code);
  },
  
  ApplyFiltersFromUrl: function() {
    const params = new URLSearchParams(window.location.search);
    
    const searchText = params.get('search');
    if (searchText) {
      $('#inputFriendSearch').val(searchText);
      ExchangeManager.SearchAndDisplay(searchText);
    }
  },
  
  UpdateUrlParameters: function() {
    const params = new URLSearchParams();
    
    if (ExchangeManager._currentSearchText) {
      params.set('search', ExchangeManager._currentSearchText);
    }

    const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`;
    window.history.replaceState({}, '', newUrl);
  }
};

