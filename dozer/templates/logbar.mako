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
<div style="width: 100%; border: 1px solid #999; padding: 3px;">
    <a href="#" onclick="javascript:DLV.show_events();">View log events for this request</a>
</div>
<div id="DLVlogevents" style="display:none;">
    <table style="width: 100%; overflow: auto; background-color: #ddd">
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
                <td style="background-color: ${bgcolor};">${event.getMessage()}</td>
            </tr>
        % endfor
        <tr style="text-align: left; vertical-align: top; border-bottom: 1px solid #333; background-color: #eee; color: #222;">
            <th colspan="2">Total Time:</th>
            <td colspan="4">${'%03d' % (1000*tottime)}ms</td>
        </tr>
        </tbody>
    </table>
</div>
<script>
var DLV = {};
DLV.getEBI = function(id, d) {
    return (d || document).getElementById(id);
};
DLV.show_events = function(elem) {
    elem = DLV.getEBI('DLVlogevents');
    if (elem.style.display == 'block') {
        elem.style.display = 'none';
    } else {
        elem.style.display = 'block';
    }
    return false;
};
</script>