<?php
/**
 * Comments.
 *
 * @package lyk7
 */

if ( post_password_required() ) {
	return;
}
?>
<section class="comments" id="comments">
	<?php if ( have_comments() ) : ?>
		<h2 class="comments__title">Σχόλια (<?php echo (int) get_comments_number(); ?>)</h2>
		<ol class="comments__list"><?php wp_list_comments( array( 'style' => 'ol', 'short_ping' => true ) ); ?></ol>
		<?php the_comments_pagination(); ?>
	<?php endif; ?>
	<?php comment_form(); ?>
</section>
