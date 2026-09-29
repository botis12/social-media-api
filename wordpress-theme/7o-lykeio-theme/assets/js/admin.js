/**
 * Media pickers for the document file and announcement attachments.
 */
( function ( $ ) {
	'use strict';

	var i18n = window.lyk7Admin || {};

	/* Single file: document */
	$( '[data-lyk7-file]' ).each( function () {
		var box = $( this );
		var input = box.find( '[data-lyk7-file-input]' );
		var name = box.find( '[data-lyk7-file-name]' );
		var clear = box.find( '[data-lyk7-file-clear]' );
		var frame = null;

		box.on( 'click', '[data-lyk7-file-pick]', function ( e ) {
			e.preventDefault();

			if ( ! frame ) {
				frame = wp.media( {
					title: i18n.pickFile,
					button: { text: i18n.use },
					multiple: false
				} );

				frame.on( 'select', function () {
					var file = frame.state().get( 'selection' ).first().toJSON();
					input.val( file.id );
					name.empty().append( $( '<strong>' ).text( file.title ) ).append( document.createTextNode( ' — ' + file.filename ) );
					clear.prop( 'hidden', false );
				} );
			}

			frame.open();
		} );

		clear.on( 'click', function ( e ) {
			e.preventDefault();
			input.val( '' );
			name.empty().append( $( '<em>' ).text( '—' ) );
			clear.prop( 'hidden', true );
		} );
	} );

	/* Multiple files: announcement attachments */
	$( '[data-lyk7-files]' ).each( function () {
		var box = $( this );
		var input = box.find( '[data-lyk7-files-input]' );
		var list = box.find( '[data-lyk7-files-list]' );
		var frame = null;

		function sync() {
			var ids = list.children( 'li' ).map( function () {
				return $( this ).data( 'id' );
			} ).get();
			input.val( ids.join( ',' ) );
		}

		box.on( 'click', '[data-lyk7-files-add]', function ( e ) {
			e.preventDefault();

			if ( ! frame ) {
				frame = wp.media( {
					title: i18n.pickFiles,
					button: { text: i18n.use },
					multiple: 'add'
				} );

				frame.on( 'select', function () {
					frame.state().get( 'selection' ).each( function ( model ) {
						var file = model.toJSON();
						if ( list.children( '[data-id="' + file.id + '"]' ).length ) {
							return;
						}
						var li = $( '<li>' ).attr( 'data-id', file.id );
						li.append( '<span class="dashicons dashicons-media-default"></span> ' );
						li.append( document.createTextNode( file.title + ' ' ) );
						li.append( $( '<button type="button" class="button-link" data-lyk7-files-remove>' ).text( i18n.remove ) );
						list.append( li );
					} );
					sync();
				} );
			}

			frame.open();
		} );

		box.on( 'click', '[data-lyk7-files-remove]', function ( e ) {
			e.preventDefault();
			$( this ).closest( 'li' ).remove();
			sync();
		} );
	} );
} )( jQuery );
