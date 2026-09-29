/**
 * Instant narrowing of the document list.
 *
 * Progressive enhancement only: the form still submits and is filtered
 * server-side without this file. Here we simply hide rows that do not match,
 * so typing feels immediate on the page the visitor already has.
 */
(function () {
	'use strict';

	var form = document.querySelector( '[data-doc-filters]' );
	var list = document.querySelector( '[data-doc-list]' );

	if ( ! form || ! list ) {
		return;
	}

	var search = form.querySelector( '[data-doc-search]' );
	var kind = form.querySelector( '[data-doc-kind]' );
	var year = form.querySelector( '[data-doc-year]' );
	var status = form.querySelector( '[data-doc-status]' );
	var empty = document.querySelector( '[data-doc-empty]' );
	var rows = Array.prototype.slice.call( list.querySelectorAll( '.doc' ) );

	if ( ! rows.length ) {
		return;
	}

	/**
	 * Strip Greek accents so "εξετασεις" matches "εξετάσεις".
	 */
	function fold( value ) {
		return value
			.toLowerCase()
			.normalize( 'NFD' )
			.replace( /[̀-ͯ]/g, '' );
	}

	var timer = null;

	function apply() {
		var q = search ? fold( search.value.trim() ) : '';
		var k = kind ? kind.value : '';
		var y = year ? year.value : '';
		var shown = 0;

		rows.forEach( function ( row ) {
			var matches = true;

			if ( q && fold( row.getAttribute( 'data-title' ) || '' ).indexOf( q ) === -1 ) {
				matches = false;
			}
			if ( matches && k && row.getAttribute( 'data-kind' ) !== k ) {
				matches = false;
			}
			if ( matches && y && row.getAttribute( 'data-year' ) !== y ) {
				matches = false;
			}

			row.hidden = ! matches;
			if ( matches ) {
				shown++;
			}
		} );

		if ( empty ) {
			empty.hidden = shown !== 0;
		}

		if ( status ) {
			var i18n = window.lyk7Docs || {};
			// Greek needs the singular form; '1 έγγραφα' is wrong.
			var template = shown === 1 ? ( i18n.one || '1' ) : ( i18n.many || '%s' );
			status.textContent = shown ? template.replace( '%s', shown ) : '';
		}
	}

	function debounced() {
		window.clearTimeout( timer );
		timer = window.setTimeout( apply, 140 );
	}

	if ( search ) {
		search.addEventListener( 'input', debounced );
	}

	/*
	 * The selects filter live, so the page does not reload while someone is
	 * exploring. The submit button remains for the no-JS path and for sharing
	 * a filtered URL.
	 */
	[ kind, year ].forEach( function ( select ) {
		if ( select ) {
			select.addEventListener( 'change', apply );
		}
	} );
})();
