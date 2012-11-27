<%!
import time
converter = time.localtime
def format_time(record, start, prev_record=None):
    if prev_record:
        delta_from_prev = (record.created - prev_record.created) * 1000
        return '%+dms' % delta_from_prev
    else:
        time_from_start = (record.created - start) * 1000
        return '%+dms' % time_from_start

def bg_color(event, log_colors):
    if event.name in log_colors:
        return log_colors[event.name]
    for key in log_colors:
        if event.name.startswith(key):
            return log_colors[key]
    return '#fff'

def fg_color(frame, traceback_colors):
    for key in traceback_colors:
        if key in frame:
            return traceback_colors[key]
    return None
%>

<div style="width: 100%; position: absolute; top:0; left: 0; z-index: 200000; font-size:11px;">
    <div style="width: 100%; background-color: #fff; border: 1px solid #999; padding: 3px; cursor: pointer;" onclick="javascript:DLV.show_events('DLVlogevents');">\
        View log events for this request
        <span style="position: absolute; top: 4px; right: 4px">${'%d' % (1000*tottime)}ms</span>
    </div>
<div id="DLVlogevents" style="display:none;">
    <table style="width: 100%; overflow: auto; background-color: #ddd;padding:2px;">
        <thead>
            <tr>
                <th colspan="2">Time</th>
                <th>Level</th>
                <th>Module</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody>
        <% prev_event = None %>
        % for event in events:
        <% bgcolor = bg_color(event, logcolors) %>
            <tr style="text-align: left; vertical-align: top; border-bottom: 1px solid #333; background-color: ${bgcolor}; color: #222;">
                <td style="background-color: ${bgcolor}; text-align: right;">${format_time(event, start)}</td>
                <td style="background-color: ${bgcolor}; text-align: right;">${format_time(event, start, prev_event)}</td>
                <td style="background-color: ${bgcolor};">${event.levelname}</td>
                <td style="background-color: ${bgcolor};">${event.name}</td>
                <td style="background-color: ${bgcolor};">\
                    <%
                        msg = event.full_message
                        length_limit = 130
                        keep_last = 70
                        if len(msg) > length_limit:
                            use_split = True
                            first = msg[:length_limit - keep_last]
                            middle = msg[length_limit - keep_last:-keep_last]
                            last = msg[-keep_last:]
                        else:
                            use_split = False
                    %>
                    % if use_split:
                        <span style="cursor: pointer; text-decoration: underline;" onclick="javascript:DLV.show_span(${id(event)})">${first}</span>\
<span style="display:inline;" id="${id(event)}_extra"> ... </span><span id="${id(event)}" style="display:none">${middle}</span>${last}
                    % else:
                        ${msg}\
                    % endif
                    % if hasattr(event, 'traceback'):
                    <span style="float: right; cursor: pointer; text-decoration: underline; margin-left: 6px;" onclick="javascript:DLV.show_block('${'tb%s' % id(event)}')">TB</span>
                    % endif
                    % if hasattr(event, 'exc_traceback'):
                    <span style="float: right; cursor: pointer; text-decoration: underline;" onclick="javascript:DLV.show_block('${'exc%s' % id(event)}')">Exception</span>
                    % endif
                    % if hasattr(event, 'exc_traceback'):
                    <pre id="${'exc%s' % id(event)}" style="display: none; padding-top: 1em">
Traceback (most recent call last):
                        % for frame in event.exc_traceback:
<% fgcolor = fg_color(frame, traceback_colors) %>\
                            % if fgcolor:
<span style="color: ${fgcolor}">${frame}</span>\
                            % else:
${frame}\
                            % endif
                        % endfor
${getattr(event.exc_info[0], '__name__', '???')}: ${event.exc_info[1]}
</pre>
                    % endif
                    % if hasattr(event, 'traceback'):
                    <pre id="${'tb%s' % id(event)}" style="display: none; padding-top: 1em">
                        % for frame in event.traceback:
<% fgcolor = fg_color(frame, traceback_colors) %>\
                            % if fgcolor:
<span style="color: ${fgcolor}">${frame}</span>\
                            % else:
${frame}\
                            % endif
                        % endfor
</pre>
                    % endif
                </td>
            </tr>
        <% prev_event = event %>
        % endfor
        <tr style="text-align: left; vertical-align: top; border-bottom: 1px solid #333; background-color: #eee; color: #222;">
            <th colspan="2">Total Time:</th>
            <td colspan="4">${'%d' % (1000*tottime)}ms</td>
        </tr>
        </tbody>
    </table>
</div>
</div>
<script>
var DLV = {};
DLV.getEBI = function(id, d) {
    return (d || document).getElementById(id);
};
DLV.show_events = function(name) {
    var elem = DLV.getEBI(name);
    if (elem.style.display == 'block') {
        elem.style.display = 'none';
    } else {
        elem.style.display = 'block';
    }
    return false;
};
DLV.show_span = function(name) {
    var elem = DLV.getEBI(name);
    if (elem.style.display == 'inline') {
        elem.style.display = 'none';
    } else {
        elem.style.display = 'inline';
    }
    elem = DLV.getEBI(name+'_extra');
    if (elem.style.display == 'inline') {
        elem.style.display = 'none';
    } else {
        elem.style.display = 'inline';
    }
    return false;
};
DLV.show_block = function(name) {
    var elem = DLV.getEBI(name);
    if (elem.style.display == 'block') {
        elem.style.display = 'none';
    } else {
        elem.style.display = 'block';
    }
    return false;
};
</script>
