<?php
/**
 * Homepage.
 *
 * @package lyk7
 */

get_header();

$lyk7_ann_url  = get_post_type_archive_link( 'anakoinosi' );
$lyk7_docs_url = get_post_type_archive_link( 'eggrafo' );
?>

<section class="hero" data-parallax-scene>
	<div class="hero__media" data-parallax-layer data-depth="0.12">
		<img src="<?php echo esc_url( lyk7_image_url( 'hero_image', 'assets/images/school-05.jpg' ) ); ?>" alt="<?php echo esc_attr( lyk7_opt( 'hero_alt' ) ); ?>" width="2000" height="1125" fetchpriority="high" decoding="async">
	</div>
	<div class="hero__wash" aria-hidden="true"></div>

	<div class="wrap hero__inner">
		<div class="hero__panel" data-parallax-layer data-depth="-0.05">
			<?php if ( lyk7_opt( 'hero_eyebrow' ) ) : ?>
				<p class="eyebrow hero__eyebrow"><?php echo esc_html( lyk7_opt( 'hero_eyebrow' ) ); ?></p>
			<?php endif; ?>

			<h1 class="hero__title">
				<span class="hero__title-top"><?php echo esc_html( lyk7_opt( 'hero_top' ) ); ?></span>
				<span class="hero__title-main"><?php echo esc_html( lyk7_opt( 'hero_main' ) ); ?></span>
			</h1>

			<?php if ( lyk7_opt( 'hero_text' ) ) : ?>
				<p class="hero__text"><?php echo esc_html( lyk7_opt( 'hero_text' ) ); ?></p>
			<?php endif; ?>

			<div class="hero__actions">
				<a class="btn btn--primary" href="<?php echo esc_url( $lyk7_ann_url ); ?>">Ανακοινώσεις <?php lyk7_icon( 'arrow', 17 ); ?></a>
				<a class="btn btn--secondary" href="<?php echo esc_url( $lyk7_docs_url ); ?>">Έγγραφα και αρχεία</a>
			</div>
		</div>
	</div>

	<div class="hero__edge" aria-hidden="true"></div>
</section>

<?php
$lyk7_deadline = lyk7_next_deadline();
$lyk7_period   = lyk7_current_period();
if ( $lyk7_deadline || $lyk7_period ) :
	?>
	<section class="today" aria-label="Σήμερα στο σχολείο">
		<div class="wrap today__inner">
			<?php if ( $lyk7_period ) : ?>
				<p class="today__item today__item--time">
					<?php lyk7_icon( 'clock', 19 ); ?>
					<span>Τώρα: <strong><?php echo esc_html( $lyk7_period[0] ); ?></strong> (<?php echo esc_html( $lyk7_period[1] . '–' . $lyk7_period[2] ); ?>)</span>
				</p>
			<?php endif; ?>
			<?php if ( $lyk7_deadline ) : ?>
				<?php $lyk7_dl = get_post_meta( $lyk7_deadline->ID, '_lyk7_deadline', true ); ?>
				<p class="today__item today__item--deadline">
					<?php lyk7_icon( 'calendar', 19 ); ?>
					<span>
						Προθεσμία <time datetime="<?php echo esc_attr( $lyk7_dl ); ?>"><?php echo esc_html( lyk7_date_compact( $lyk7_dl ) ); ?></time>
						— <a href="<?php echo esc_url( get_permalink( $lyk7_deadline ) ); ?>"><?php echo esc_html( get_the_title( $lyk7_deadline ) ); ?></a>
					</span>
				</p>
			<?php endif; ?>
		</div>
	</section>
<?php endif; ?>

<section class="section section--board" id="anakoinoseis">
	<div class="wrap">
		<header class="section__head">
			<div>
				<p class="eyebrow">Ενημέρωση</p>
				<h2 class="section__title">Πίνακας ανακοινώσεων</h2>
			</div>
			<a class="btn btn--ghost" href="<?php echo esc_url( $lyk7_ann_url ); ?>">Όλες οι ανακοινώσεις <?php lyk7_icon( 'arrow', 16 ); ?></a>
		</header>

		<?php
		$lyk7_featured = get_posts(
			array(
				'post_type'      => 'anakoinosi',
				'posts_per_page' => 1,
				'meta_key'       => '_lyk7_urgent',
				'meta_value'     => '1',
			)
		);
		$lyk7_list = new WP_Query(
			array(
				'post_type'           => 'anakoinosi',
				'posts_per_page'      => $lyk7_featured ? 4 : 5,
				'post__not_in'        => $lyk7_featured ? array( $lyk7_featured[0]->ID ) : array(),
				'no_found_rows'       => true,
				'ignore_sticky_posts' => true,
			)
		);

		if ( ! $lyk7_featured && $lyk7_list->have_posts() ) {
			$lyk7_featured = array( array_shift( $lyk7_list->posts ) );
			--$lyk7_list->post_count;
		}

		if ( $lyk7_featured ) :
			?>
			<div class="board board--split" data-tilt-scene>
				<?php
				global $post;
				$post = $lyk7_featured[0]; // phpcs:ignore WordPress.WP.GlobalVariablesOverride
				setup_postdata( $post );
				get_template_part( 'template-parts/card-announcement', null, array( 'variant' => 'featured' ) );
				wp_reset_postdata();
				?>
				<div class="board__list">
					<?php
					while ( $lyk7_list->have_posts() ) :
						$lyk7_list->the_post();
						get_template_part( 'template-parts/card-announcement' );
					endwhile;
					wp_reset_postdata();
					?>
				</div>
			</div>
		<?php else : ?>
			<?php lyk7_empty( 'Δεν υπάρχουν ακόμη ανακοινώσεις.' ); ?>
		<?php endif; ?>
	</div>
</section>

<?php $lyk7_quick = lyk7_parse_lines( lyk7_opt( 'quick' ), 4 ); ?>
<?php if ( $lyk7_quick ) : ?>
<section class="section section--quick" aria-labelledby="quick-title">
	<div class="wrap">
		<header class="section__head section__head--tight">
			<div>
				<p class="eyebrow">Συντομεύσεις</p>
				<h2 class="section__title" id="quick-title">Γρήγορη πρόσβαση</h2>
			</div>
		</header>

		<ul class="quick-grid">
			<?php foreach ( $lyk7_quick as $lyk7_tile ) : ?>
				<?php
				$lyk7_href = lyk7_resolve_url( $lyk7_tile[2] );
				$lyk7_out  = 0 === strpos( $lyk7_href, 'http' ) && false === strpos( $lyk7_href, (string) wp_parse_url( home_url(), PHP_URL_HOST ) );
				?>
				<li class="quick-tile" data-reveal>
					<a href="<?php echo esc_url( $lyk7_href ); ?>"<?php echo $lyk7_out ? ' target="_blank" rel="noopener noreferrer"' : ''; ?>>
						<span class="quick-tile__icon"><?php lyk7_icon( $lyk7_tile[3] ? $lyk7_tile[3] : 'arrow', 26 ); ?></span>
						<span class="quick-tile__label"><?php echo esc_html( $lyk7_tile[0] ); ?></span>
						<?php if ( $lyk7_tile[1] ) : ?>
							<span class="quick-tile__desc"><?php echo esc_html( $lyk7_tile[1] ); ?></span>
						<?php endif; ?>
					</a>
				</li>
			<?php endforeach; ?>
		</ul>
	</div>
</section>
<?php endif; ?>

<section class="section section--about" aria-labelledby="about-title">
	<div class="wrap about">
		<div class="about__media" data-reveal>
			<figure class="about__figure">
				<img src="<?php echo esc_url( lyk7_image_url( 'about_image', 'assets/images/school-18.jpg' ) ); ?>" alt="Κοινόχρηστος χώρος του σχολείου με στρογγυλά τραπέζια, μπλε καρέκλες σκηνοθέτη και ζωγραφισμένη στον τοίχο θαλασσινή τοιχογραφία" width="960" height="720" loading="lazy" decoding="async">
			</figure>
			<figure class="about__figure about__figure--inset">
				<img src="<?php echo esc_url( lyk7_image_url( 'about_image2', 'assets/images/school-13.jpg' ) ); ?>" alt="Τοιχογραφία μαθητών που απεικονίζει πλακιώτικο σοκάκι με πέτρινα σκαλοπάτια" width="960" height="720" loading="lazy" decoding="async">
			</figure>
		</div>

		<div class="about__body" data-reveal>
			<p class="eyebrow">Ταυτότητα</p>
			<h2 class="section__title" id="about-title">Το σχολείο μας</h2>

			<?php if ( lyk7_opt( 'about_lead' ) ) : ?>
				<p class="about__lead"><?php echo esc_html( lyk7_opt( 'about_lead' ) ); ?></p>
			<?php endif; ?>

			<?php $lyk7_timeline = lyk7_parse_lines( lyk7_opt( 'timeline' ), 2 ); ?>
			<?php if ( $lyk7_timeline ) : ?>
				<ol class="timeline">
					<?php foreach ( $lyk7_timeline as $lyk7_row ) : ?>
						<li class="timeline__item">
							<span class="timeline__year"><?php echo esc_html( $lyk7_row[0] ); ?></span>
							<span class="timeline__text"><?php echo esc_html( $lyk7_row[1] ); ?></span>
						</li>
					<?php endforeach; ?>
				</ol>
			<?php endif; ?>

			<?php $lyk7_about = get_page_by_path( 'to-scholeio-mas' ); ?>
			<?php if ( $lyk7_about ) : ?>
				<a class="btn btn--secondary" href="<?php echo esc_url( get_permalink( $lyk7_about ) ); ?>">Περισσότερα για το σχολείο</a>
			<?php endif; ?>
		</div>
	</div>
</section>

<?php
$lyk7_life = new WP_Query(
	array(
		'post_type'      => 'drastiriotita',
		'posts_per_page' => 4,
		'no_found_rows'  => true,
		'meta_query'     => array(
			'relation' => 'OR',
			'ev'       => array( 'key' => '_lyk7_event_date', 'compare' => 'EXISTS' ),
			array( 'key' => '_lyk7_event_date', 'compare' => 'NOT EXISTS' ),
		),
		'orderby'        => array( 'ev' => 'DESC', 'date' => 'DESC' ),
	)
);
if ( $lyk7_life->have_posts() ) :
	?>
	<section class="section section--life" aria-labelledby="life-title">
		<div class="wrap">
			<header class="section__head">
				<div>
					<p class="eyebrow">Δράσεις και εκδηλώσεις</p>
					<h2 class="section__title" id="life-title">Η ζωή του σχολείου</h2>
				</div>
				<a class="btn btn--ghost" href="<?php echo esc_url( get_post_type_archive_link( 'drastiriotita' ) ); ?>">Όλες οι δραστηριότητες <?php lyk7_icon( 'arrow', 16 ); ?></a>
			</header>

			<div class="life-grid" data-tilt-scene>
				<?php
				while ( $lyk7_life->have_posts() ) :
					$lyk7_life->the_post();
					get_template_part( 'template-parts/card-activity', null, array( 'large' => 0 === $lyk7_life->current_post ) );
				endwhile;
				wp_reset_postdata();
				?>
			</div>
		</div>
	</section>
<?php endif; ?>

<?php
$lyk7_docs = new WP_Query( array( 'post_type' => 'eggrafo', 'posts_per_page' => 6, 'no_found_rows' => true ) );
if ( $lyk7_docs->have_posts() ) :
	?>
	<section class="section section--docs" aria-labelledby="docs-title">
		<div class="wrap">
			<header class="section__head">
				<div>
					<p class="eyebrow">Αρχείο</p>
					<h2 class="section__title" id="docs-title">Έγγραφα και αρχεία</h2>
					<p class="section__lede"><?php echo esc_html( lyk7_opt( 'docs_lede' ) ); ?></p>
				</div>
				<a class="btn btn--ghost" href="<?php echo esc_url( $lyk7_docs_url ); ?>">Όλα τα έγγραφα <?php lyk7_icon( 'arrow', 16 ); ?></a>
			</header>

			<ul class="doc-list">
				<?php
				while ( $lyk7_docs->have_posts() ) :
					$lyk7_docs->the_post();
					get_template_part( 'template-parts/doc-row' );
				endwhile;
				wp_reset_postdata();
				?>
			</ul>
		</div>
	</section>
<?php endif; ?>

<?php
$lyk7_gallery = new WP_Query( array( 'post_type' => 'gallery_item', 'posts_per_page' => 6, 'no_found_rows' => true, 'orderby' => array( 'menu_order' => 'ASC', 'date' => 'DESC' ) ) );
if ( $lyk7_gallery->have_posts() ) :
	?>
	<section class="section section--gallery" aria-labelledby="gallery-title">
		<div class="wrap">
			<header class="section__head">
				<div>
					<p class="eyebrow">Εικόνες</p>
					<h2 class="section__title" id="gallery-title">Στιγμιότυπα</h2>
				</div>
				<a class="btn btn--ghost" href="<?php echo esc_url( get_post_type_archive_link( 'gallery_item' ) ); ?>">Όλη η συλλογή <?php lyk7_icon( 'arrow', 16 ); ?></a>
			</header>

			<ul class="mosaic" data-gallery>
				<?php
				while ( $lyk7_gallery->have_posts() ) :
					$lyk7_gallery->the_post();
					get_template_part( 'template-parts/mosaic-item' );
				endwhile;
				wp_reset_postdata();
				?>
			</ul>
		</div>
	</section>
<?php endif; ?>

<?php get_template_part( 'template-parts/contact' ); ?>

<?php
get_footer();
