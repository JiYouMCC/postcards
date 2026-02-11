function RefreshPopoverListeners() {
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  const popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
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
    popoverTriggerEl.addEventListener('shown.bs.popover', function() {
      let language_code = "en";
      if (Cookies.get("local_language_code")) {
        language_code = Cookies.get("local_language_code");
      }
      localize.localize(language_code);
    });
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
        const mode = popoverTriggerEl.getAttribute('data-card-mode') || "";
        let fromOrTo = `<strong data-localize="From">From</strong>`;
        let usernameParam = "sender";
        if (mode == "sent") {
          fromOrTo = `<strong data-localize="To">To</strong>`;
          usernameParam = "receiver";
        }
        const location = region ? `<a href="${mode}?countries=${country}" style="cursor: pointer;" data-localize="${country}">${country}</a> - <a href="${mode}?countries=${country}&regions=${region}" style="cursor: pointer;" data-localize="${region}">${region}</a>` : `<a href="${mode}?countries=${country}" target="_blank" style="cursor: pointer;" data-localize="${country}">${country}</a>`;
        let resultHtml = `<a href="${cardUrl}" target="_blank" title="${cardUrl}"><strong>${cardTitle}</strong></a>`;
        resultHtml += `<br>${fromOrTo} <a href="${mode}?&${usernameParam}=${friendId}" style="cursor: pointer;">${friendId}</a><a href="${friendUrl}" target="_blank" class="text-decoration-none" style="cursor: pointer;" title="${friendUrl}">🔗</a> (${location})`;
        resultHtml += `<br><strong data-localize="On">On</strong> <a href="${mode}?platforms=${platform}" style="cursor: pointer;">${platform}</a>`;
        resultHtml += `<br><strong data-localize="By">By</strong> <a href="${mode}?types=${cardType}" style="cursor: pointer;" data-localize="${cardType}">${cardType}</a>`;
        resultHtml += `<br>${sentDataStr} ~`;
        if (receivedDate) {
          resultHtml += ` ${receivedDataStr} (${days} <span data-localize="day(s)">day(s)</span>)<br>`;
        } else {
          resultHtml += ` <span data-localize="Expired">Expired</span><br>`;
        }
        tags.split(' ').forEach(tag => {
          resultHtml += `<a href="${mode}?tags=${tag}" style="cursor: pointer;"><span class="me-1 badge text-bg-primary">${tag}</span></a>`;
        });
        return resultHtml;
      }
    })
  });
}
RefreshPopoverListeners();