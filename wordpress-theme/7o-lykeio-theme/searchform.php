<?php
/**
 * Search form.
 *
 * @package lyk7
 */

$lyk7_id = wp_unique_id( 'search-field-' );
?>
<form role="search" method="get" class="search-form" action="<?php echo esc_url( home_url( '/' ) ); ?>">
	<label class="screen-reader-text" for="<?php echo esc_attr( $lyk7_id ); ?>">Αναζήτηση στον ιστότοπο</label>
	<div class="search-form__row">
		<input type="search" id="<?php echo esc_attr( $lyk7_id ); ?>" class="search-form__input" value="<?php echo esc_attr( get_search_query() ); ?>" name="s" placeholder="Αναζήτηση σε ανακοινώσεις, έγγραφα, δράσεις…" autocomplete="off">
		<button type="submit" class="search-form__submit">
			<?php lyk7_icon( 'search', 19 ); ?>
			<span>Αναζήτηση</span>
		</button>
	</div>
</form>
