function Debounce(func, wait) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

function Capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
};

const PostcardCollection = {
  _postData: undefined,
  _filterData: undefined,
  _itemsPerPage: 24,
  _currentPage: 1,
  _baseUrl: "/postcards/",
  Init: function(data) {
    PostcardCollection._postData = data.sort((a, b) => new Date(b['sent_date']) - new Date(a['sent_date']));
    PostcardCollection._postData.forEach(item => {
      item['tags'] = item['tags'] ? item['tags'].split(' ') : [];
    });
    PostcardCollection._filterData = PostcardCollection._postData;
    PostcardCollection.RefreshFilterElements(PostcardCollection._filterData);
    PostcardCollection.RefreshImageContainer();
    PostcardCollection.InitFilterElements();
    PostcardCollection.ApplyFiltersFromUrl();
  },
  _UpdateDropdownText: function(selector, text) {
    if (text.length > 3) {
      text = text.slice(0, 3).join(', ').concat('...(' + text.length + ')');
    } else {
      text = text.join(', ');
    }
    $(selector).text(text || Capitalize(selector.split('-')[1]));
  },
  InitFilterElements: function() {
    const handleCheckboxChange = (allSelector, itemSelector, dropdownSelector) => {
      $(allSelector).on('change', function() {
        const isChecked = $(this).is(':checked');
        $(itemSelector).prop('checked', isChecked);
      });

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
    };

    handleCheckboxChange('#country-all', '#ul-country .form-check-input', '#dropdownMenuButton-country');
    handleCheckboxChange('#region-all', '#ul-region .form-check-input', '#dropdownMenuButton-region');
    handleCheckboxChange('#type-all', '#ul-type .form-check-input', '#dropdownMenuButton-type');
    handleCheckboxChange('#platform-all', '#ul-platform .form-check-input', '#dropdownMenuButton-platform');

    // country和region联动
    $('#ul-country .form-check-input').on('change', function() {
      const selectedCountries = $('#ul-country .form-check-input:checked').not('#country-all').map(function() {
        return $(this).val();
      }).get();
      const selectedRegions = $('#ul-region .form-check-input:checked').not('#region-all').map(function() {
        return $(this).val();
      }).get();

      const regionList = new Set();
      if (selectedCountries.length === 0) {
        PostcardCollection._postData.forEach(item => {
          if (item['region']) {
            regionList.add(item['region']);
          }
        });
      } else {
        PostcardCollection._postData.filter(item => selectedCountries.includes(item['country'])).forEach(item => {
          if (item['region']) {
            regionList.add(item['region']);
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

      const sortedRegionList = Array.from(regionList).sort((a, b) => {
        const textA = a.toLowerCase();
        const textB = b.toLowerCase();
        return textA.localeCompare(textB, 'zh-CN');
      });

      sortedRegionList.forEach(region => {
        $('#ul-region').append(
          $("<li></li>").append(
            $("<div></div>").addClass("dropdown-item").append(
              $("<input></input>").addClass("form-check-input me-1").attr("type", "checkbox").attr("value", region).attr("id", `region_${region}`),
              $("<label></label>").addClass("form-check-label").attr("for", `region_${region}`).text(region)
            )
          )
        );
        if (selectedRegions.includes(region))
          $(`#region_${region}`).prop('checked', true);
      });

      const selectedOptions = $('#ul-region .form-check-input:checked').not('#region-all').map(function() {
        return $(this).val();
      }).get();

      handleCheckboxChange('#region-all', '#ul-region .form-check-input', '#dropdownMenuButton-region');

      PostcardCollection._UpdateDropdownText('#dropdownMenuButton-region', selectedOptions);

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
    $("#inputTitle,#inputReceiver").width("12ch");

    $("#inputTitle,#inputReceiver").on('input', function(event) {
      function getStringWidth(str) {
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
      $(this).width(Math.max(getStringWidth($(this).val()), 12) + "ch");
    });

    // input挂钩
    $("#inputTitle,#inputReceiver").on('input', Debounce(() => {
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
      $('#inputTitle, #inputReceiver, #inputSentDateStart, #inputSentDateEnd, #inputReceivedDateStart, #inputReceivedDateEnd').val('');
      $('#ul-country .form-check-input, #ul-region .form-check-input, #ul-type .form-check-input, #ul-platform .form-check-input, #div-tags .form-check-input').prop('checked', false);
      PostcardCollection._UpdateDropdownText('#dropdownMenuButton-country', []);
      PostcardCollection._UpdateDropdownText('#dropdownMenuButton-region', []);
      PostcardCollection._UpdateDropdownText('#dropdownMenuButton-type', []);
      PostcardCollection._UpdateDropdownText('#dropdownMenuButton-platform', []);
      $("#inputTitle,#inputReceiver").width("12ch");
      new bootstrap.Collapse('#collapseTags', {toggle: false}).hide();
      new bootstrap.Collapse('#collapseSentDate', {toggle: false}).hide();
      new bootstrap.Collapse('#collapseReceivedDate', {toggle: false}).hide();
      PostcardCollection._currentPage = 1;
      PostcardCollection.GenerateFilter();
      PostcardCollection.RefreshImageContainer();
      PostcardCollection.UpdateUrlParameters();
    });

    //parameter update
    $('#ul-country .form-check-input, #ul-region .form-check-input, #ul-type .form-check-input, #ul-platform .form-check-input, #inputTitle, #inputReceiver, #div-tags .form-check-input, #collapseSentDate .form-control, #collapseReceivedDate .form-control').on('change input', function() {
      PostcardCollection.UpdateUrlParameters();
    });
  },
  ApplyFiltersFromUrl: function() {
    const params = new URLSearchParams(window.location.search);
    const setCheckboxValues = (selector, values) => {
      values.forEach(value => {
        const checkbox = $(`${selector}[value="${value}"]`);
        if (checkbox.length) {
          checkbox.prop('checked', true);
        }
      });
    };

    const countries = params.get('countries')?.split(',') || [];
    const regions = params.get('regions')?.split(',') || [];
    const types = params.get('types')?.split(',') || [];
    const platforms = params.get('platforms')?.split(',') || [];
    const tags = params.get('tags')?.split(',') || [];
    const title = params.get('title') || '';
    const receiver = params.get('receiver') || '';
    const sentDateStart = params.get('sentDateStart') || '';
    const sentDateEnd = params.get('sentDateEnd') || '';
    const receivedDateStart = params.get('receivedDateStart') || '';
    const receivedDateEnd = params.get('receivedDateEnd') || '';
    const page = params.get('page') || 1;

    setCheckboxValues('#ul-country .form-check-input', countries);
    setCheckboxValues('#ul-region .form-check-input', regions);
    setCheckboxValues('#ul-type .form-check-input', types);
    setCheckboxValues('#ul-platform .form-check-input', platforms);
    setCheckboxValues('#div-tags .form-check-input', tags);

    $('#inputTitle').val(title);
    $('#inputReceiver').val(receiver);
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
    const updateList = (selector, items, idPrefix) => {
      if (idPrefix === 'tag') {
        items.forEach(item => {
          $(selector).append(
            $("<div></div").addClass('d-flex flex-wrap').append(
              $("<input></input>").addClass("form-check-input me-1").attr("type", "checkbox").attr("value", item).attr("id", `${idPrefix}_${item}`),
              $("<label></label>").addClass("form-check-label me-2").attr("for", `${idPrefix}_${item}`).text(item)
            )
          )
        });
      } else {
        const sortedItems = Array.from(items).sort((a, b) => {
          const textA = a.toLowerCase();
          const textB = b.toLowerCase();
          return textA.localeCompare(textB, 'zh-CN');
        });
        sortedItems.forEach(item => {
          $(selector).append(
            $("<li></li>").append(
              $("<div></div>").addClass("dropdown-item").append(
                $("<input></input>").addClass("form-check-input me-1").attr("type", "checkbox").attr("value", item).attr("id", `${idPrefix}_${item}`),
                $("<label></label>").addClass("form-check-label").attr("for", `${idPrefix}_${item}`).text(item)
              )
            )
          );
        });
      }
    };

    $("#cardCount").text(PostcardCollection._postData.length);
    $("#searchCount").text(data.length);

    const countryList = new Set();
    const typeList = new Set();
    const platformList = new Set();
    const friendList = new Set();
    const regionList = new Set();
    const tagList = new Set();

    data.forEach(item => {
      if (item['country']) countryList.add(item['country']);
      if (item['type']) typeList.add(item['type']);
      if (item['platform']) platformList.add(item['platform']);
      if (item['friend_id']) friendList.add(item['friend_id']);
      if (item['region']) regionList.add(item['region']);
      if (item['tags']) item['tags'].forEach(tag => tagList.add(tag));
    });

    updateList("#ul-country", countryList, 'country');
    updateList("#ul-type", typeList, 'type');
    updateList("#ul-platform", platformList, 'platform');
    updateList("#ul-region", regionList, 'region');
    updateList("#div-tags", tagList, 'tag');

    friendList.forEach(friend => {
      $("#datalistReceiver").append($("<option></option>").attr("value", friend));
    });
    const options = $("#datalistReceiver option").toArray();
    options.sort((a, b) => {
      const textA = $(a).attr("value").toLowerCase();
      const textB = $(b).attr("value").toLowerCase();
      return textA.localeCompare(textB, 'zh-CN');
    });
    $("#datalistReceiver").empty();
    options.forEach(option => {
      $("#datalistReceiver").append(option);
    });
  },
  RefreshPopoverListeners: function() {
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
          resultHtml += `<br><strong>To</strong> <a href="?&receiver=${friendId}" style="cursor: pointer;">${friendId}</a><a href="${friendUrl}" target="_blank" class="text-decoration-none" style="cursor: pointer;" title="${friendUrl}">🔗</a> (${location})`;
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
    const getSelectedValues = (selector) => $(selector + ':checked').not(selector + '-all').map(function() {
      return $(this).val();
    }).get();

    const selectedCountries = getSelectedValues('#ul-country .form-check-input');
    const selectedRegions = getSelectedValues('#ul-region .form-check-input');
    const selectedTypes = getSelectedValues('#ul-type .form-check-input');
    const selectedPlatforms = getSelectedValues('#ul-platform .form-check-input');
    const selectedTags = getSelectedValues('#div-tags .form-check-input');
    const selectedFriend = $('#inputReceiver').val();
    const selectedTitle = $('#inputTitle').val();
    const sentDateStart = $('#inputSentDateStart').val();
    const sentDateEnd = $('#inputSentDateEnd').val();
    const receivedDateStart = $('#inputReceivedDateStart').val();
    const receivedDateEnd = $('#inputReceivedDateEnd').val();

    PostcardCollection._filterData = PostcardCollection._postData.filter(item => {
      const isTitleMatch = !selectedTitle || (item['title'] && item['title'].includes(selectedTitle)) || (item['id'] && item['id'].includes(selectedTitle)) || item['tags'].some(tag => tag.includes(selectedTitle));
      const isCountryMatch = !selectedCountries.length || selectedCountries.includes(item['country']);
      const isRegionMatch = !selectedRegions.length || selectedRegions.includes(item['region']);
      const isTypeMatch = !selectedTypes.length || selectedTypes.includes(item['type']);
      const isPlatformMatch = !selectedPlatforms.length || selectedPlatforms.includes(item['platform']);
      const isTagMatch = !selectedTags.length || selectedTags.some(tag => item['tags'].includes(tag));
      const isFriendMatch = !selectedFriend || (item['friend_id'] && item['friend_id'].includes(selectedFriend));
      const isSentDateMatch = (!sentDateStart || new Date(item['sent_date']) >= new Date(sentDateStart)) && (!sentDateEnd || new Date(item['sent_date']) <= new Date(sentDateEnd));
      const isReceivedDateMatch = (!receivedDateStart || new Date(item['received_date']) >= new Date(receivedDateStart)) && (!receivedDateEnd || new Date(item['received_date']) <= new Date(receivedDateEnd));
      return isTitleMatch && isCountryMatch && isRegionMatch && isTypeMatch && isPlatformMatch && isTagMatch && isFriendMatch && isSentDateMatch && isReceivedDateMatch;
    });
  },
  RefreshPagenation: function() {
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

    // receiver
    const receiver = $('#inputReceiver').val();
    if (receiver) {
      params.set('receiver', receiver);
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