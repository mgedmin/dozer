<%inherit file="layout.mako"/>
<h1>All Profiles</h1>
<a href="/_profiler/delete">Delete all</a>
<table>
    <tr>
        <td>URL</td>
        <td>Time</td>
        <td>Profile ID</td>
    </tr>
    % for created_time, environ, profile_id in profiles:
    <tr pid="${profile_id}">
        <td>${environ['SCRIPT_NAME'] + environ['PATH_INFO'] + environ['QUERY_STRING']|h}</td>
        <td>${'%i' % int(now-created_time)} seconds ago</td>
        <td><a href="/_profiler/show/${profile_id}">${profile_id}</a></td>
        <td><a href="/_profiler/delete/${profile_id}" class="delete">delete</a></td>
    </tr>
    % endfor
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
      }
    });
    return false;
});
</script>
</%def>
