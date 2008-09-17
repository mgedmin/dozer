<%!
import time
converter = time.localtime
def format_time(record):
    ct = converter(record.created)
    t = time.strftime('%H:%M:%S', ct)
    return '%s,%03d' % (t, record.msecs)

def bg_color(event, log_colors):
    for key in log_colors:
        if key == event.name:
            return log_colors[key]
    for key in log_colors:
        if event.name.startswith(key):
            return log_colors[key]
    return '#fff'
%>

<div style="width: 100%; position: absolute; top:0; left: 0; z-index: 200000; font-size:11px;">
    <div style="width: 100%; background-color: #fff; border: 1px solid #999; padding: 3px; cursor: pointer;" onclick="javascript:DLV.show_events('DLVlogevents');">\
        View log events for this request
    </div>
<div id="DLVlogevents" style="display:none;">
    <table style="width: 100%; overflow: auto; background-color: #ddd;padding:2px;">
        <thead>
            <tr>
                <th>Time</th>
                <th>Level</th>
                <th>Module</th>
                <th>Message</th>
            </tr>
        </thead>
        <tbody>
        % for event in events:
        <% bgcolor = bg_color(event, logcolors) %>
            <tr style="text-align: left; vertical-align: top; border-bottom: 1px solid #333; background-color: ${bgcolor}; color: #222;">
                <td style="background-color: ${bgcolor};">${format_time(event)}</td>
                <td style="background-color: ${bgcolor};">${event.levelname}</td>
                <td style="background-color: ${bgcolor};">${event.name}</td>
                <td style="background-color: ${bgcolor};">\
                    <% 
                        msg = event.getMessage()
                        length_limit = 130
                        if len(msg) > length_limit:
                            use_split = True
                            first = msg[:length_limit]
                            last = msg[length_limit:]
                        else:
                            use_split = False
                            parts = None
                    %>
                    % if use_split:
                        <span style="cursor: pointer; text-decoration: underline;" onclick="javascript:DLV.show_span(${id(event)})">${first}</span>\
<span style="display:inline;" id="${id(event)}_extra">...</span><span id="${id(event)}" style="display:none">${last}</span>
                    % else:
                        ${msg | h}\
                    % endif
                </td>
            </tr>
        % endfor
        <tr style="text-align: left; vertical-align: top; border-bottom: 1px solid #333; background-color: #eee; color: #222;">
            <th colspan="2">Total Time:</th>
            <td colspan="4">${'%03d' % (1000*tottime)}ms</td>
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
</script>