// ------- 工具类函数 -------

function Debounce(func, wait) {
  // 防抖函数
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

function Capitalize(str) {
  // 首字母大写
  return str.charAt(0).toUpperCase() + str.slice(1);
};

function GetStringWidth(str) {
  // 计算字符串宽度，CJP字符算2，其他算1
  let width = 0;
  for (let char of str) {
    if (char.match(/[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]/)) {
      // CJP characters
      width += 2;
    } else {
      // English characters
      width += 1;
    }
  }
  return width;
}

const PostcardCollection = {
  _postData: undefined,
  _filterData: undefined,
  _itemsPerPage: 24,
  _currentPage: 1,
  _baseUrl: "/postcards/",
  Init: function(data) {
    // 初始化数据
    PostcardCollection._postData = data.sort((a, b) => new Date(b['received_date']) - new Date(a['received_date']));
    PostcardCollection._postData.forEach(item => {
      item['tags'] = item['tags'] ? item['tags'].split(' ') : [];
    });

    // 初始化过滤器
    PostcardCollection._filterData = PostcardCollection._postData;
    PostcardCollection.RefreshFilterElements(PostcardCollection._filterData);
    PostcardCollection.RefreshImageContainer();
    PostcardCollection.InitFilterElements();
    PostcardCollection.ApplyFiltersFromUrl();
  },
  // ------ UI 相关函数 ------
  _UpdateDropdownText: function(selector, text) {
    // 更新下拉菜单文本
    if (text.length > 3) {
      text = text.slice(0, 3).join(', ').concat('...(' + text.length + ')');
    } else {
      text = text.join(', ');
    }

    // 如果是Region, 默认文本为 "Region/City"
    if (selector === '#dropdownMenuButton-region' && !text) {
      text = 'Region / City';
    } else {
      $(selector).text(text || Capitalize(selector.split('-')[1]));
    }
  },

  _HandleCheckboxChange: function(allSelector, itemSelector, dropdownSelector) {
    // 处理复选框变化
    $(allSelector).off('change');
    $(allSelector).on('change', function() {
      const isChecked = $(this).is(':checked');
      $(itemSelector).prop('checked', isChecked);
    });
    $(itemSelector).off('change');
    $(itemSelector).not(allSelector).on('change', function() {
      const allChecked = $(itemSelector).not(allSelector).length === $(itemSelector).not(allSelector).filter(':checked').length;
      $(allSelector).prop('checked', allChecked);
    });

    $(itemSelector).on('change', function() {
      const selectedOptions = $(itemSelector + ':checked').not(allSelector).map(function() {
        return $(this).val();
      }).get();
      PostcardCollection._UpdateDropdownText(dropdownSelector, selectedOptions);
    });
  },

  _SetCheckboxValues: function(selector, values) {
    // 设置复选框值
    values.forEach(value => {
      const checkbox = $(`${selector}[value="${value}"]`);
      if (checkbox.length) {
        checkbox.prop('checked', true);
      }
    });
  },

  _UpdateDrowdownList: function(selector, items, idPrefix) {
    // tag 专用    
    if (idPrefix === 'tag') {
      //$(selector).empty();
      //排序
      const sortedItems = Array.from(items).sort((a, b) => {
        const tagA = a.toLowerCase();
        const tagB = b.toLowerCase();
        return tagA.localeCompare(tagB, 'zh-CN');
      });
      sortedItems.forEach(item => {
        $(selector).append(
          $("<div></div").addClass('d-flex flex-wrap').append(
            $("<input></input>").addClass("form-check-input me-1").attr("type", "checkbox").attr("value", item).attr("id", `${idPrefix}_${item}`),
            $("<label></label>").addClass("form-check-label me-2").attr("for", `${idPrefix}_${item}`).text(item)
          )
        )
      });
    }
  },

  _UpdateDropDownListFromMap: function(selector, map, idPrefix) {
    // 通用版
    const items = Array.from(map.entries()).sort((a, b) => {
      const countryA = a[0].toLowerCase();
      const countryB = b[0].toLowerCase();
      return countryA.localeCompare(countryB, 'zh-CN');
    });
    //$(selector).empty();
    items.forEach(([region, count]) => {
      $(selector).append(
        $("<li></li>").append(
          $("<div></div>").addClass("dropdown-item d-flex justify-content-between align-items-center").append(
            $("<div></div>").append(
              $("<input></input>").addClass("form-check-input me-1").attr("type", "checkbox").attr("value", region).attr("id", `${idPrefix}_${region}`),
              $("<label></label>").addClass("form-check-label").attr("for", `${idPrefix}_${region}`).text(`${region}`)
            ),
            $("<span></span>").addClass("badge rounded-pill bg-secondary ms-2").text(`${count}`)
          )
        )
      );
    });
  },

  // ------ 主要功能函数 ------
  InitFilterElements: function() {
    // 初始化过滤器元素事件
    PostcardCollection._HandleCheckboxChange('#country-all', '#ul-country .form-check-input', '#dropdownMenuButton-country');
    PostcardCollection._HandleCheckboxChange('#region-all', '#ul-region .form-check-input', '#dropdownMenuButton-region');
    PostcardCollection._HandleCheckboxChange('#type-all', '#ul-type .form-check-input', '#dropdownMenuButton-type');
    PostcardCollection._HandleCheckboxChange('#platform-all', '#ul-platform .form-check-input', '#dropdownMenuButton-platform');

    // country和region联动
    $('#ul-country .form-check-input').on('change', function() {
      const selectedCountries = $('#ul-country .form-check-input:checked').not('#country-all').map(function() {
        return $(this).val();
      }).get();
      const selectedRegions = $('#ul-region .form-check-input:checked').not('#region-all').map(function() {
        return $(this).val();
      }).get();

      const regionMap = new Map();

      if (selectedCountries.length === 0) {
        // 全选
        PostcardCollection._postData.forEach(item => {
          if (item['region']) {
            if (!regionMap.has(item['region'])) {
              regionMap.set(item['region'], 0);
            }
            regionMap.set(item['region'], regionMap.get(item['region']) + 1);
          }
        });
      } else {
        PostcardCollection._postData.filter(item => selectedCountries.includes(item['country'])).forEach(item => {
          if (item['region']) {
            if (!regionMap.has(item['region'])) {
              regionMap.set(item['region'], 0);
            }
            regionMap.set(item['region'], regionMap.get(item['region']) + 1);
          }
        });
      }

      $('#ul-region').empty();
      $('#ul-region').append(
        $("<li></li>").append(
          $("<div></div>").addClass("dropdown-item").append(
            $("<input></input>").addClass("form-check-input me-1").attr("type", "checkbox").attr("value", "all").attr("id", "region-all"),
            $("<label></label>").addClass("form-check-label").attr("for", "region-all").text("All")
          )
        )
      );

      PostcardCollection._UpdateDropDownListFromMap("#ul-region", regionMap, 'region');
      selectedRegions.forEach(region => {
        if ($(`#region_${region}`).length) {
          $(`#region_${region}`).prop('checked', true);
        }
      });

      const selectedOptions = $('#ul-region .form-check-input:checked').not('#region-all').map(function() {
        return $(this).val();
      }).get();

      PostcardCollection._HandleCheckboxChange('#region-all', '#ul-region .form-check-input', '#dropdownMenuButton-region');
      PostcardCollection._UpdateDropdownText('#dropdownMenuButton-region', selectedOptions);

      $('#ul-region .form-check-input').off('change');
      $('#ul-region .form-check-input').on('change', Debounce(() => {
        PostcardCollection.GenerateFilter();
        PostcardCollection.RefreshImageContainer();
        PostcardCollection.UpdateUrlParameters();
      }, 100));
    });

    $('#tag-all').on('change', function() {
      const isChecked = $(this).is(':checked');
      $('#div-tags .form-check-input').prop('checked', isChecked);
    });

    // input 尺寸
    $("#inputTitle,#inputSender").width("12ch");
    $("#inputTitle,#inputSender").on('input', function(event) {
      $(this).width(Math.max(GetStringWidth($(this).val()), 12) + "ch");
    });

    // input挂钩
    $("#inputTitle,#inputSender").on('input', Debounce(() => {
      PostcardCollection.GenerateFilter();
      PostcardCollection.RefreshImageContainer();
    }, 100));

    // 其他checkbox和日期挂钩
    $('#ul-country .form-check-input, #ul-region .form-check-input, #ul-type .form-check-input, #ul-platform .form-check-input, #div-tags .form-check-input, #collapseSentDate .form-control, #collapseReceivedDate .form-control').on('change', Debounce(() => {
      PostcardCollection.GenerateFilter();
      PostcardCollection.RefreshImageContainer();
    }, 100));

    // reset
    $('#resetFilter').on('click', () => {
      $('#inputTitle, #inputSender, #inputSentDateStart, #inputSentDateEnd, #inputReceivedDateStart, #inputReceivedDateEnd').val('');
      $('#ul-country .form-check-input, #ul-region .form-check-input, #ul-type .form-check-input, #ul-platform .form-check-input, #div-tags .form-check-input').prop('checked', false);
      PostcardCollection._UpdateDropdownText('#dropdownMenuButton-country', []);
      PostcardCollection._UpdateDropdownText('#dropdownMenuButton-region', []);
      PostcardCollection._UpdateDropdownText('#dropdownMenuButton-type', []);
      PostcardCollection._UpdateDropdownText('#dropdownMenuButton-platform', []);
      // 重置region list
      const regionMap = new Map();
      PostcardCollection._postData.forEach(item => {
        if (item['region']) {
          if (!regionMap.has(item['region'])) {
            regionMap.set(item['region'], 0);
          }
          regionMap.set(item['region'], regionMap.get(item['region']) + 1);
        }
      });
      PostcardCollection._UpdateDropDownListFromMap("#ul-region", regionMap, 'region');
      $("#inputTitle,#inputSender").width("12ch");
      new bootstrap.Collapse('#collapseTags', {
        toggle: false
      }).hide();
      new bootstrap.Collapse('#collapseSentDate', {
        toggle: false
      }).hide();
      new bootstrap.Collapse('#collapseReceivedDate', {
        toggle: false
      }).hide();
      PostcardCollection._currentPage = 1;
      PostcardCollection.GenerateFilter();
      PostcardCollection.RefreshImageContainer();
      PostcardCollection.UpdateUrlParameters();
    });

    //parameter update
    $('#ul-country .form-check-input, #ul-region .form-check-input, #ul-type .form-check-input, #ul-platform .form-check-input, #inputTitle, #inputSender, #div-tags .form-check-input, #collapseSentDate .form-control, #collapseReceivedDate .form-control').on('change input', function() {
      PostcardCollection.UpdateUrlParameters();
    });
  },
  ApplyFiltersFromUrl: function() {
    // 从URL应用过滤器
    const params = new URLSearchParams(window.location.search);

    const countries = params.get('countries')?.split(',') || [];
    const regions = params.get('regions')?.split(',') || [];
    const types = params.get('types')?.split(',') || [];
    const platforms = params.get('platforms')?.split(',') || [];
    const tags = params.get('tags')?.split(',') || [];
    const title = params.get('title') || '';
    const sender = params.get('sender') || '';
    const sentDateStart = params.get('sentDateStart') || '';
    const sentDateEnd = params.get('sentDateEnd') || '';
    const receivedDateStart = params.get('receivedDateStart') || '';
    const receivedDateEnd = params.get('receivedDateEnd') || '';
    const page = params.get('page') || 1;

    PostcardCollection._SetCheckboxValues('#ul-country .form-check-input', countries);
    PostcardCollection._SetCheckboxValues('#ul-region .form-check-input', regions);
    PostcardCollection._SetCheckboxValues('#ul-type .form-check-input', types);
    PostcardCollection._SetCheckboxValues('#ul-platform .form-check-input', platforms);
    PostcardCollection._SetCheckboxValues('#div-tags .form-check-input', tags);

    if (countries.length) {
      $('#ul-country .form-check-input:checked').first().trigger('change');
    }

    $('#inputTitle').val(title);
    $('#inputSender').val(sender);
    $('#inputSentDateStart').val(sentDateStart);
    $('#inputSentDateEnd').val(sentDateEnd);
    $('#inputReceivedDateStart').val(receivedDateStart);
    $('#inputReceivedDateEnd').val(receivedDateEnd);


    const selectedCountries = $("#ul-country .form-check-input" + ':checked').not("#country-all").map(function() {
      return $(this).val();
    }).get();
    PostcardCollection._UpdateDropdownText('#dropdownMenuButton-country', selectedCountries);

    const selectedRegions = $("#ul-region .form-check-input" + ':checked').not("#region-all").map(function() {
      return $(this).val();
    }).get();
    PostcardCollection._UpdateDropdownText('#dropdownMenuButton-region', selectedRegions);

    const selectedTypes = $("#ul-type .form-check-input" + ':checked').not("#type-all").map(function() {
      return $(this).val();
    }).get();
    PostcardCollection._UpdateDropdownText('#dropdownMenuButton-type', selectedTypes);

    const selectedPlatforms = $("#ul-platform .form-check-input" + ':checked').not("#platform-all").map(function() {
      return $(this).val();
    }).get();
    PostcardCollection._UpdateDropdownText('#dropdownMenuButton-platform', selectedPlatforms);

    PostcardCollection.GenerateFilter();
    // apply the page
    PostcardCollection._currentPage = page;
    const totalPages = Math.ceil(PostcardCollection._filterData.length / PostcardCollection._itemsPerPage);
    const currentPage = Math.min(PostcardCollection._currentPage, totalPages);
    PostcardCollection._currentPage = Math.max(currentPage, 1);
    PostcardCollection.GeneratePagination(currentPage, totalPages);
    const startIndex = (currentPage - 1) * PostcardCollection._itemsPerPage;
    const endIndex = startIndex + PostcardCollection._itemsPerPage;
    PostcardCollection.GenerateImageContainer(PostcardCollection._filterData.slice(startIndex, endIndex));
    $("#pagination .page-item").removeClass("active");
    $("#pagination .page-link").each(function() {
      if ($(this).attr("data-page") == currentPage) {
        $(this).parent().addClass("active");
      }
    });
    $("#cardstart").text(Math.min(PostcardCollection._filterData.length, (PostcardCollection._currentPage - 1) * PostcardCollection._itemsPerPage + 1));
    $("#cardend").text(Math.min(PostcardCollection._currentPage * PostcardCollection._itemsPerPage, PostcardCollection._filterData.length));
    $("#cardCount").text(PostcardCollection._postData.length);
    $("#searchCount").text(PostcardCollection._filterData.length);
  },
  RefreshFilterElements: function(data) {
    // 刷新过滤器元素
    $("#cardCount").text(PostcardCollection._postData.length);
    $("#searchCount").text(data.length);

    const countryMap = new Map();
    const typeMap = new Map();
    const platformMap = new Map();
    const friendList = new Set();
    const regionMap = new Map();
    const tagList = new Set();

    data.forEach(item => {
      if (item['country']) {
        if (!countryMap.has(item['country'])) {
          countryMap.set(item['country'], 0);
        }
        countryMap.set(item['country'], countryMap.get(item['country']) + 1);
      }

      if (item['type']) {
        if (!typeMap.has(item['type'])) {
          typeMap.set(item['type'], 0);
        }
        typeMap.set(item['type'], typeMap.get(item['type']) + 1);
      }

      if (item['platform']) {
        if (!platformMap.has(item['platform'])) {
          platformMap.set(item['platform'], 0);
        }
        platformMap.set(item['platform'], platformMap.get(item['platform']) + 1);
      }

      if (item['friend_id']) friendList.add(item['friend_id']);
      if (item['region']) {
        if (!regionMap.has(item['region'])) {
          regionMap.set(item['region'], 0);
        }
        regionMap.set(item['region'], regionMap.get(item['region']) + 1);
      }

      if (item['tags']) item['tags'].forEach(tag => tagList.add(tag));
    });

    PostcardCollection._UpdateDropDownListFromMap("#ul-country", countryMap, 'country');
    PostcardCollection._UpdateDropDownListFromMap("#ul-type", typeMap, 'type');
    PostcardCollection._UpdateDropDownListFromMap("#ul-platform", platformMap, 'platform');
    PostcardCollection._UpdateDropDownListFromMap("#ul-region", regionMap, 'region');
    PostcardCollection._UpdateDrowdownList("#div-tags", tagList, 'tag');

    friendList.forEach(friend => {
      $("#datalistSender").append($("<option></option>").attr("value", friend));
    });
    const options = $("#datalistSender option").toArray();
    options.sort((a, b) => {
      const textA = $(a).attr("value").toLowerCase();
      const textB = $(b).attr("value").toLowerCase();
      return textA.localeCompare(textB, 'zh-CN');
    });
    $("#datalistSender").empty();
    options.forEach(option => {
      $("#datalistSender").append(option);
    });
  },
  RefreshPopoverListeners: function() {
    // 刷新 Popover 监听器
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl);
    });
    popoverList.forEach(function(popover) {
      popover.dispose();
    });
    const newpopoverList = popoverTriggerList.map(function(popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl, {
        html: true,
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
          const receivedDate = new Date(popoverTriggerEl.getAttribute('data-card-received_date'));
          const tags = popoverTriggerEl.getAttribute('data-card-tags') || "";
          const platform = popoverTriggerEl.getAttribute('data-card-platform');
          const days = Math.floor((receivedDate - sentDate) / (1000 * 60 * 60 * 24));
          const sentDataStr = `${sentDate.getFullYear()}-${sentDate.getMonth() + 1}-${sentDate.getDate()}`;
          const receivedDataStr = `${receivedDate.getFullYear()}-${receivedDate.getMonth() + 1}-${receivedDate.getDate()}`;
          const location = region ? `<a href="?countries=${country}" style="cursor: pointer;">${country}</a> - <a href="?countries=${country}&regions=${region}" style="cursor: pointer;">${region}</a>` : `<a href="?countries=${country}" target="_blank" style="cursor: pointer;">${country}</a>`;
          let resultHtml = `<a href="${cardUrl}" target="_blank" title="${cardUrl}"><strong>${cardTitle}</strong></a>`;
          resultHtml += `<br><strong>From</strong> <a href="?&sender=${friendId}" style="cursor: pointer;">${friendId}</a><a href="${friendUrl}" target="_blank" class="text-decoration-none" style="cursor: pointer;" title="${friendUrl}">🔗</a> (${location})`;
          resultHtml += `<br><strong>On</strong> <a href="?platforms=${platform}" style="cursor: pointer;">${platform}</a>`;
          resultHtml += `<br><strong>By</strong> <a href="?types=${cardType}" style="cursor: pointer;">${cardType}</a>`;
          resultHtml += `<br>${sentDataStr} ~ ${receivedDataStr} (${days} days)<br>`;
          tags.split(',').forEach(tag => {
            resultHtml += `<a href="?tags=${tag}" style="cursor: pointer;"><span class="me-1 badge text-bg-primary">${tag}</span></a>`;
          });
          return resultHtml;
        }
      })
    });
  },
  RefreshImageContainer: function() {
    // 刷新图片容器
    try {
      $('[data-bs-toggle="popover"]').popover('hide');
    } catch (e) {}

    $("#cardCount").text(PostcardCollection._postData.length);
    $("#searchCount").text(PostcardCollection._filterData.length);

    // apply the page
    const totalPages = Math.ceil(PostcardCollection._filterData.length / PostcardCollection._itemsPerPage);
    const currentPage = Math.min(PostcardCollection._currentPage, totalPages);
    PostcardCollection._currentPage = Math.max(currentPage, 1);
    PostcardCollection.GeneratePagination(currentPage, totalPages);
    const startIndex = (currentPage - 1) * PostcardCollection._itemsPerPage;
    const endIndex = startIndex + PostcardCollection._itemsPerPage;
    PostcardCollection.GenerateImageContainer(PostcardCollection._filterData.slice(startIndex, endIndex));
    //PostcardCollection.GenerateImageContainer(PostcardCollection._filterData);
    //PostcardCollection.RefreshPagenation()
    $("#pagination .page-item").removeClass("active");
    $("#pagination .page-link").each(function() {
      if ($(this).attr("data-page") == currentPage) {
        $(this).parent().addClass("active");
      }
    });
    $("#cardstart").text(Math.min(PostcardCollection._filterData.length, (PostcardCollection._currentPage - 1) * PostcardCollection._itemsPerPage + 1));
    $("#cardend").text(Math.min(currentPage * PostcardCollection._itemsPerPage, PostcardCollection._filterData.length));
  },
  GenerateImageContainer: function(data) {
    // 生成图片容器
    $("#imageContainer").empty();
    data.forEach(dataItem => {
      $("#imageContainer").append(
        $("<div></div>").attr("id", "image_" + dataItem['id']).addClass("col-lg-2 col-md-4 mb-2 col-6 image-item px-1").append(
          $("<img></img>").addClass("img-fluid img-thumbnail postcard")
          .attr("src", PostcardCollection._baseUrl + `received/${dataItem['id']}.jpg`)
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
        ));
    });
    // 在所有图片上添加 onerror 事件
    document.querySelectorAll('img').forEach(img => {
      img.onerror = function() {
        this.src = PostcardCollection._baseUrl + '/postcard.svg'; // 替换为默认图片的路径
      };
    });

    PostcardCollection.RefreshPopoverListeners();
  },
  GenerateFilter: function() {
    // 生成过滤器
    const getSelectedValues = (selector) => $(selector + ':checked').not(selector + '-all').map(function() {
      return $(this).val();
    }).get();

    const selectedCountries = getSelectedValues('#ul-country .form-check-input');
    const selectedRegions = getSelectedValues('#ul-region .form-check-input');
    const selectedTypes = getSelectedValues('#ul-type .form-check-input');
    const selectedPlatforms = getSelectedValues('#ul-platform .form-check-input');
    const selectedTags = getSelectedValues('#div-tags .form-check-input');
    const selectedFriend = $('#inputSender').val();
    const selectedTitle = $('#inputTitle').val();
    const sentDateStart = $('#inputSentDateStart').val();
    const sentDateEnd = $('#inputSentDateEnd').val();
    const receivedDateStart = $('#inputReceivedDateStart').val();
    const receivedDateEnd = $('#inputReceivedDateEnd').val();
    let selectedFriendUrl = [];
    if (selectedFriend) {
      let itemList = PostcardCollection._postData.filter(item => item['friend_id'] && item['friend_id'].includes(selectedFriend))
      selectedFriendUrl = itemList.map(item => item['friend_url']);
      selectedFriendUrl = Array.from(new Set(selectedFriendUrl));
    }

    PostcardCollection._filterData = PostcardCollection._postData.filter(item => {
      const isTitleMatch = !selectedTitle || (item['title'] && item['title'].includes(selectedTitle)) || (item['id'] && item['id'].includes(selectedTitle)) || (item['friend_id'] && item['friend_id'].includes(selectedTitle)) || (item['friend_url'] && item['friend_url'].includes(selectedTitle)) || item['tags'].some(tag => tag.includes(selectedTitle));
      const isCountryMatch = !selectedCountries.length || selectedCountries.includes(item['country']);
      const isRegionMatch = !selectedRegions.length || selectedRegions.includes(item['region']);
      const isTypeMatch = !selectedTypes.length || selectedTypes.includes(item['type']);
      const isPlatformMatch = !selectedPlatforms.length || selectedPlatforms.includes(item['platform']);
      const isTagMatch = !selectedTags.length || selectedTags.some(tag => item['tags'].includes(tag));
      const isFriendUrlMatch = !selectedFriend || (item['friend_url'] && selectedFriendUrl.includes(item['friend_url']));
      const isSentDateMatch = (!sentDateStart || new Date(item['sent_date']) >= new Date(sentDateStart)) && (!sentDateEnd || new Date(item['sent_date']) <= new Date(sentDateEnd));
      const isReceivedDateMatch = (!receivedDateStart || new Date(item['received_date']) >= new Date(receivedDateStart)) && (!receivedDateEnd || new Date(item['received_date']) <= new Date(receivedDateEnd));
      return isTitleMatch && isCountryMatch && isRegionMatch && isTypeMatch && isPlatformMatch && isTagMatch && isFriendUrlMatch && isSentDateMatch && isReceivedDateMatch;
    });
  },
  RefreshPagenation: function() {
    // 刷新分页
    const totalPages = Math.ceil(PostcardCollection._filterData.length / PostcardCollection._itemsPerPage);
    const paginationContainer = $("#pagination");
    paginationContainer.empty();
    const page = 1;
    const startIndex = (page - 1) * PostcardCollection._itemsPerPage;
    const endIndex = startIndex + PostcardCollection._itemsPerPage;
    PostcardCollection.GeneratePagination(page, totalPages);
    PostcardCollection.GenerateImageContainer(PostcardCollection._filterData.slice(startIndex, endIndex));
  },
  GeneratePagination: function(currentPage, totalPages) {
    // 生成分页
    try {
      $('[data-bs-toggle="popover"]').popover('hide');
    } catch (e) {}
    const paginationContainer = $("#pagination");
    paginationContainer.empty();
    PostcardCollection._currentPage = Math.max(currentPage, 1);
    const firstPageItem = $("<li></li>").addClass("page-item").append(
      $("<a></a>").addClass("page-link").text(1).attr("href", "#").attr("data-page", 1)
    );
    paginationContainer.append(firstPageItem);

    if (totalPages > 4 && PostcardCollection._currentPage > 3) {
      const dotsItem = $("<li></li>").addClass("page-item").append(
        $("<a></a>").addClass("page-link disabled").text("...").attr("href", "#").attr("data-page", "...")
      );
      paginationContainer.append(dotsItem);
    }

    const startPage = Math.max(2, PostcardCollection._currentPage - 2);
    const endPage = Math.min(totalPages - 1, PostcardCollection._currentPage + 2);
    for (let i = startPage; i <= endPage; i++) {
      const pageItem = $("<li></li>").addClass("page-item").append(
        $("<a></a>").addClass("page-link").text(i).attr("href", "#").attr("data-page", i)
      );
      paginationContainer.append(pageItem);
    }

    if (totalPages > 4 && PostcardCollection._currentPage < totalPages - 2) {
      const dotsItem = $("<li></li>").addClass("page-item").append(
        $("<a></a>").addClass("page-link disabled").text("...").attr("href", "#").attr("data-page", "...")
      );
      paginationContainer.append(dotsItem);
    }

    if (totalPages > 1) {
      const lastPageItem = $("<li></li>").addClass("page-item").append(
        $("<a></a>").addClass("page-link").text(totalPages).attr("href", "#").attr("data-page", totalPages)
      );
      paginationContainer.append(lastPageItem);
    }

    paginationContainer.find(".page-item").removeClass("active");
    paginationContainer.find(".page-link").each(function() {
      if ($(this).attr("data-page") == PostcardCollection._currentPage) {
        $(this).parent().addClass("active");
      }
    });

    paginationContainer.find(".page-link").on("click", function(event) {
      event.preventDefault();
      const totalPages = Math.ceil(PostcardCollection._filterData.length / PostcardCollection._itemsPerPage);
      const page = parseInt($(this).attr("data-page"));
      const startIndex = (page - 1) * PostcardCollection._itemsPerPage;
      const endIndex = startIndex + PostcardCollection._itemsPerPage;
      PostcardCollection.GeneratePagination(page, totalPages);
      PostcardCollection.GenerateImageContainer(PostcardCollection._filterData.slice(startIndex, endIndex));
      PostcardCollection.UpdateUrlParameters();
    });

    $("#cardstart").text(Math.min(PostcardCollection._filterData.length, (PostcardCollection._currentPage - 1) * PostcardCollection._itemsPerPage + 1));
    $("#cardend").text(Math.min(PostcardCollection._currentPage * PostcardCollection._itemsPerPage, PostcardCollection._filterData.length));
  },
  UpdateUrlParameters: function() {
    // 更新URL参数
    const params = new URLSearchParams();

    // country
    const selectedCountries = $('#ul-country .form-check-input:checked').not('#country-all').map(function() {
      return $(this).val();
    }).get();
    if (selectedCountries.length) {
      params.set('countries', selectedCountries.join(','));
    }

    // region
    const selectedRegions = $('#ul-region .form-check-input:checked').not('#region-all').map(function() {
      return $(this).val();
    }).get();
    if (selectedRegions.length) {
      params.set('regions', selectedRegions.join(','));
    }

    // type
    const selectedTypes = $('#ul-type .form-check-input:checked').not('#type-all').map(function() {
      return $(this).val();
    }).get();
    if (selectedTypes.length) {
      params.set('types', selectedTypes.join(','));
    }

    // platform
    const selectedPlatforms = $('#ul-platform .form-check-input:checked').not('#platform-all').map(function() {
      return $(this).val();
    }).get();
    if (selectedPlatforms.length) {
      params.set('platforms', selectedPlatforms.join(','));
    }

    // title
    const title = $('#inputTitle').val();
    if (title) {
      params.set('title', title);
    }

    // sender
    const sender = $('#inputSender').val();
    if (sender) {
      params.set('sender', sender);
    }

    // tags
    const tags = $('#div-tags .form-check-input:checked').not('#tag-all').map(function() {
      return $(this).val();
    }).get();
    if (tags.length) {
      params.set('tags', tags.join(','));
    }

    //sent date
    const sentDateStart = $('#inputSentDateStart').val();
    if (sentDateStart) {
      params.set('sentDateStart', sentDateStart);
    }

    const sentDateEnd = $('#inputSentDateEnd').val();
    if (sentDateEnd) {
      params.set('sentDateEnd', sentDateEnd);
    }

    // received date
    const receivedDateStart = $('#inputReceivedDateStart').val();
    if (receivedDateStart) {
      params.set('receivedDateStart', receivedDateStart);
    }

    const receivedDateEnd = $('#inputReceivedDateEnd').val();
    if (receivedDateEnd) {
      params.set('receivedDateEnd', receivedDateEnd);
    }

    // page
    const currentPage = PostcardCollection._currentPage;
    if (currentPage && currentPage > 1) {
      params.set('page', currentPage);
    }

    const newUrl = `${window.location.pathname}?${params.toString()}`;
    history.replaceState(null, '', newUrl);
  }
}