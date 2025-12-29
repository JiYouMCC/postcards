---
title: localize js
---
// refer: https://github.com/coderifous/jquery-localize

var localize = {
  json_cache: {},
  language_setting: {
    "languages": [{
      "title": "English",
      "file": "{{ site.baseurl }}{{ '/lg/basic-en.json' }}",
      "code": "en"
    }, {
      "title": "中文",
      "file": "{{ site.baseurl }}{{ '/lg/basic-zh.json' }}",
      "code": "zh"
    }, ]
  },
  default_language: "zh",
  getLanguageJson: function(language, callback) {
        var self = this;
        if (self.json_cache[language]) {
          json = self.json_cache[language];
          callback(json);
        } else {
          var jsonFile;
          for (var i = 0; i < self.language_setting.languages.length; i++) {
            if (self.language_setting.languages[i].code == language) {
              jsonFile = self.language_setting.languages[i].file;
              break;
            }
          }
          if (jsonFile) {
            $.getJSON(jsonFile, function(data) {
              self.json_cache[language] = data;
              callback(data);
            }).fail(function() {
              callback(undefined);
            });
          } else {
            callback(undefined);
          }
        }
  },
  languageSupported: function(language) {
        var self = this;
        var result = false;
        for (var i = 0; i < self.language_setting.languages.length; i++) {
          if (self.language_setting.languages[i].code == language) {
            result = true;
            break;
          }
        }
        return result;
  },
  localize: function(language, callback) {
    var self = this;
    self.getLanguageJson(language, function(json) {
      if (json) {
        $("[data-localize]").each(function() {
          var elem = $($(this));
          var key = elem.attr("data-localize");
          var value = json[key];
          self.localizeElement(elem, key, value);
        });
        // for tooltip, the data-bs-original-title will be html, and process it again
        $("[data-bs-toggle='tooltip']").each(function() {
          var elem = $($(this));
          var original_title = elem.attr("data-bs-original-title");
          var $elements = $(original_title);
          $elements.each(function() {
            if (!$(this).attr("data-localize")) {
              return;
            }
            var $inner_elem = $(this);
            var inner_key = $inner_elem.attr("data-localize");
            var inner_value = json[inner_key];
            localize.localizeElement($inner_elem, inner_key, inner_value);
          });
          var newTooltipString = $('<div>').append($elements. clone()).html();
          elem.attr("data-bs-original-title", newTooltipString);
        });
        if (callback) {
          callback();
        }
      } else {
        if (callback) {
          callback();
        }
      }
    });
  },
  localizeElement: function(elem, key, value) {
        if (elem.is('input')) {
          return this.localizeInputElement(elem, key, value);
        } else if (elem.is('textarea')) {
          return this.localizeInputElement(elem, key, value);
        } else if (elem.is('img')) {
          return this.localizeImageElement(elem, key, value);
        } else if (elem.is('optgroup')) {
          return this.localizeOptgroupElement(elem, key, value);
        } else if (elem.data("data-bs-toggle") == "tooltip") {
          return this.localizeToolTipElement(elem, key, value);
        } else if (elem.is('button') && elem.is("[original-text]")) {
          elem.text(value);
          elem.attr("original-text", value);
          return;
        }
        else if (!$.isPlainObject(value)) {
          elem.html(value);
          return;
        }
        if ($.isPlainObject(value)) {
          return this.localizeForSpecialKeys(elem, value);
        }
  },
  localizeInputElement: function(elem, key, value) {
        var val;
        val = $.isPlainObject(value) ? value.value : value;
        if (elem.is("[placeholder]")) {
          return elem.attr("placeholder", val);
        } else {
          return elem.val(val);
        }
  },
  localizeOptgroupElement: function(elem, key, value) {
        return elem.attr("label", value);
  },
  localizeImageElement: function(elem, key, value) {
        this.setAttrFromValueForKey(elem, "alt", value);
        return this.setAttrFromValueForKey(elem, "src", value);
  },
  localizeToolTipElement: function(elem, key, value) {
        elem.attr("title", value);
        elem.attr("data-original-title", value);
        return elem.data("original-title", value);
  },
  localizeForSpecialKeys: function(elem, value) {
        this.setAttrFromValueForKey(elem, "title", value);
        this.setAttrFromValueForKey(elem, "href", value);
        return this.setTextFromValueForKey(elem, "text", value);
  },
  setAttrFromValueForKey: function(elem, key, value) {
        value = this.valueForKey(key, value);
        if (value != null) {
          return elem.attr(key, value);
        }
  },
  setTextFromValueForKey: function(elem, key, value) {
        value = this.valueForKey(key, value);
        if (value != null) {
          return elem.text(value);
        }
  },
  valueForKey: function(key, data) {
        var keys, value, _i, _len;
        keys = key.split(/\./);
        value = data;
        for (_i = 0, _len = keys.length; _i < _len; _i++) {
          key = keys[_i];
          value = value != null ? value[key] : null;
        }
        return value;
  },
  init: function() {
        for (var i = 0; i < this.language_setting.languages.length; i++) {
          $("#dropdown_language").append(
            $("<li></li>").append(
              $("<a></a>").attr({
                class: "dropdown-item d-flex justify-content-between",
                href: "#",
                id: 'language_' + this.language_setting.languages[i].code
              }).text(this.language_setting.languages[i].title)
            )
          );
        }

        var language_code = navigator.language.split('-')[0];
        if (!this.languageSupported(language_code)) {
          language_code = this.default_language;
        }

        if (Cookies.get("local_language_code")) {
          language_code = Cookies.get("local_language_code");
        }
        this.localize(language_code);
        return language_code;
  }
}

$(document).ready(function() {
  localize.init();
  $("[id^=language_]").click(function() {
    var language = $(this).attr('id').split('language_')[1];
    localize.localize(language, function() {
      Cookies.set("local_language_code", language);
    });
  });
});