$(document).ready(function(){
	editor = CKEDITOR.replace( 'editor');
	
//override ctrl+s function
	var isCtrl = false;
	editor.on( 'contentDom', function( evt ){
    	editor.document.on( 'keyup', function(event){
        	if(event.data.$.keyCode == 17) isCtrl=false;
   		});

    	editor.document.on( 'keydown', function(event){
        	if(event.data.$.keyCode == 17) isCtrl=true;
        	if(event.data.$.keyCode == 83 && isCtrl == true)
        	{
                //The preventDefault() call prevents the browser's save popup to appear.
                //The try statement fixes a weird IE error.
                try {
                    event.data.$.preventDefault();
                    $("#submit").click();

                } catch(err) {}
                //Call to your save function
                return false;
        	}
    	});
    });
});

function getContent(){
    return editor.getData();
}