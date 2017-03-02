$(document).ready(function(){
	/*commen event*/
	makecommenthtml=$("#comment-widget").html();
	$(".c-quote").click(function(){
		$(".c-form").remove();
		if($(this).attr("href")=="#c-new"){
			//new comment
			$("#c-new").html("")
			$("#c-new").html(makecommenthtml);
			$("#c-new").show();
		}
		else{
			//reply to someone
			$("#c-new").hide();
			$(this).parent().parent().append(makecommenthtml);
			var name=$(this).parent().children(".c-nickname").text();
			$("#newcomment").attr("placeholder","回复 "+name+"\n不支持特殊标签")
			return false;
		}
	});
});


function submitcomment(obj){
	var haserror=false;
	$("#nickname").parent().parent().removeClass("has-error");		
	$("#email").parent().parent().removeClass("has-error");		
	$("#newcomment").parent().parent().removeClass("has-error");
	$(".error-message").remove();

	$("#nickname").val($("#nickname").val().trim());
	$("#email").val($("#email").val().trim());
	if( !isValidNickname($("#nickname").val()) ){
		$("#nickname").parent().parent().addClass("has-error");
		haserror=true;
	}
	if(!isValidMail($("#email").val())){
		$("#email").parent().parent().addClass("has-error");
		haserror=true;
	}
	if($("#newcomment").val().trim()==""){
		$("#newcomment").parent().parent().addClass("has-error");
		haserror=true;
	}
	data=gen_comment_obj(obj);
	if(haserror==false){
		$.ajax({
			url:"/comment",
			type:"POST",
			data:data,
			contentType:"application/json",
			success:function(data){
				data=JSON.stringify(data);
				if (data.success==true){
					alert(data.message);
				}
				else{
					var message="<span id='tmp'>评论成功</span>";
					$("#message").html("");
					$("#message").html(message);
					$("#tmp").fadeOut(3000,document.location.reload());
				}
			},
			error:function(){
				alert("server error");
			}
		});
	}
}

function gen_comment_obj(obj){
	var newcomment={};
	newcomment.nickname=$("#nickname").val();
	newcomment.email=$("#email").val();
	newcomment.content=$("#newcomment").val();
	newcomment.website=$("#website").val();
	newcomment.parent_comment_id=null;
	obj=$(obj).parent().parent().parent().parent();
	if(!obj.hasClass("bigwidget")){
		newcomment.parent_comment_id=obj.children(".c-content").attr("_id");
	}
	newcomment.post_id=$("#post_id").val();
	newcomment=JSON.stringify(newcomment);
	return newcomment;
}