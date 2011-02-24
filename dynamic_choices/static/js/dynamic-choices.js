($ || jQuery || django.jQuery)(document).ready(function(){

	var $ = $ || jQuery || django.jQuery,
			DATA_BOUND_FIELDS = 'data-dynamic-choices-bound-fields',
      DATA_FORMSET = 'data-dynamic-choices-formset';
      
  var error = (function(){
    if ('console' in window && $.isFunction(console.error))
      return function(e) { // We must wrap the function see 
        console.error(e);
      };
    else return function(e) {
      throw new Error(e);
    };
  })();

  function getFieldNames(fields) {
    return fields.map(function(index, field){
      return field.name;
    }).toArray();
  };

  $.fn.updateFields = function(url, form) {
    var handlers = $.fn.updateFields.widgetHandlers;
    if (this.length) {
      form = $(form ? form : this[0].form);
      var fields = $(this).addClass('loading'),
          data = $(form).serializeArray(),
          boundFields = [];
      // Make sure fields bound to these ones are updated right after
      fields.each(function(i, field){
        var selector = $(field).attr(DATA_BOUND_FIELDS);
        if (selector) boundFields.push(selector);
        var formset = $(field).closest('[' + DATA_FORMSET + ']').attr(DATA_FORMSET);
        if (formset) boundFields.push($.fn.bindFieldset.formsetsBindings[formset](field));
      });
      fields.addClass('loading');
      data.push({name: 'DYNAMIC_CHOICES_FIELDS',
                value:getFieldNames(fields).join(',')});
      $.getJSON(url, $.param(data), function(json){
        fields.each(function(index, field){
          if (field.name in json) {
            var data = json[field.name];
            if (data.widget in handlers) {
              handlers[data.widget](field, data.value);
              $(field).trigger('change', {'triggeredByDynamicChoices': true});
            } else error('Missing handler for "' + data.widget + '" widget.');
          }
          $(field).removeClass('loading');
        });
        $(boundFields.join(', ')).updateFields(url, form);
      });
    }
    return this;
  };
  
  function assignOptions(element, options) {
    $(options).each(function(index, option) {
      if ($.isArray(option[1])) {
        var optGroup = $('<optgroup></optgroup>').attr({label: option[0]});
        assignOptions(optGroup, option[1]);
        element.append(optGroup);
      } else {
        element.append($('<option></option>').attr({value:option[0]}).html(option[1]));
      }
    });
  };
  
  function selectWidgetHandler(select, options) {
    select = $(select);
    var value = select.val();
    select.empty();
    assignOptions(select, options);
    select.val(value);
  };
  
  $.fn.updateFields.widgetHandlers = {
    'default': selectWidgetHandler
  };
  
  $.fn.bindFields = function(url, fields) {
    var handlers = $.fn.bindFields.widgetHandlers;
    return this.each(function(index, field){
      $(field).change(function(event, data){
      	if (data && 'triggeredByDynamicChoices' in data) return;
        $(fields).updateFields(url, field.form);
      }).attr(DATA_BOUND_FIELDS, fields);
    });
  };
  
  function defaultFieldNameExtractor(fieldset, field) {
    var match = field.match(/^([\w_]+)-(\w+)-([\w_]+)$/);
    if (match && match[1] == fieldset) {
      return {
        index: match[2],
        name: match[3]
      };
    } else error('Can\'t resolve field "' + field + '"\s of specified fieldset "' + fieldset + '".');
  };
  
  function defaultFieldSelectorBuilder(fieldset, field, index) {
    return '#id_' + fieldset + '-' + index + '-' + field;
  };
  
  function curryBuilder(fieldset, index, builder) {
    return function(i, field){
      return builder(fieldset, field, index);
    };
  };
  
  function formsetFieldBoundFields(fieldset, field, fields, extractor, builder) {
    field = extractor(fieldset, field.name);
    if (field.name in fields) {
      var selectors = $(fields[field.name]).map(curryBuilder(fieldset, field.index, builder));
      return selectors.toArray().join(', ');
    } else return '';
  };
  
  $.fn.bindFieldset = function(url, fieldset, fields, extractor, builder) {
    extractor = $.isFunction(extractor) ? extractor : defaultFieldNameExtractor;
    builder = $.isFunction(builder) ? builder : defaultFieldSelectorBuilder;
    $.fn.bindFieldset.formsetsBindings[fieldset] = function(field){
      return formsetFieldBoundFields(fieldset, field, fields, extractor, builder);
    };
    return this.each(function(index, container){
      $(container).change(function(event, data){
      	if (data && 'triggeredByDynamicChoices' in data) return;
        var target = event.target,
            selectors = formsetFieldBoundFields(fieldset, target, fields, extractor, builder);
        $(selectors).updateFields(url, target.form);
      }).attr(DATA_FORMSET, fieldset);
    });
  };
  $.fn.bindFieldset.formsetsBindings = {};
	
});
