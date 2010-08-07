<%inherit file="layout.mako"/>
<h1>All Profiles</h1>
<p><a href="/_profiler/delete">Delete all</a></p>
<table id="profile-list">
    <tr>
        <th class="url">URL</th>
        <th class="cost">Cost</th>
        <th class="time">Time</th>
        <th class="pid">Profile ID</th>
        <th class="delete"></th>
    </tr>
    % for created_time, environ, total_cost, profile_id in profiles:
    <tr pid="${profile_id}">
        <td class="url">${environ['SCRIPT_NAME'] + environ['PATH_INFO'] + environ['QUERY_STRING']|h}</td>
        <td class="cost">${total_cost} ms</td>
        <td class="time">${'%i' % int(now-created_time)} seconds ago</td>
        <td class="pid"><a href="/_profiler/show/${profile_id}">${profile_id}</a></td>
        <td class="delete"><a href="/_profiler/delete/${profile_id}" class="delete">delete</a></td>
    </tr>
    % endfor
    % if errors:
    <tr id="error-header">
        <th class="error" colspan="2">Error</th>
        <th class="time">Time</th>
        <th class="pid">Profile ID</th>
        <th class="delete"></th>
    </tr>
    % for created_time, error, profile_id in errors:
    <tr pid="${profile_id}" class="error">
        <td class="error" colspan="2">${error|h}</td>
        <td class="time">${'%i' % int(now-created_time)} seconds ago</td>
        <td class="pid">${profile_id}</td>
        <td class="delete"><a href="/_profiler/delete/${profile_id}" class="delete">delete</a></td>
    </tr>
    % endfor
    % endif
</table>

<%def name="javascript()">
${parent.javascript()}
<script>
$(".delete").click(function() {
    tr = $(this).parent().parent();
    $.ajax({
      type: "POST",
      url: "/_profiler/delete/"+tr.attr("pid"),
      success: function(msg){
        tr.remove();
        if ($("tr.error").length == 0) $("#error-header").remove();
      }
    });
    return false;
});
</script>
</%def>