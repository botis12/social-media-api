<?php
/**
 * Site header.
 *
 * @package lyk7
 */

$lyk7_phones = lyk7_phones();
$lyk7_email  = lyk7_opt( 'email' );
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link rel="profile" href="https://gmpg.org/xfn/11">
	<?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<a class="skip-link" href="#content">Μετάβαση στο περιεχόμενο</a>

<header class="site-header" id="top">

	<div class="utility-bar">
		<div class="wrap utility-bar__inner">
			<p class="utility-bar__note"><?php echo esc_html( lyk7_opt( 'address' ) ); ?></p>

			<ul class="utility-bar__links">
				<?php if ( $lyk7_phones ) : ?>
					<li>
						<a href="<?php echo esc_attr( lyk7_tel( $lyk7_phones[0][1][0] ) ); ?>">
							<?php lyk7_icon( 'phone', 15 ); ?>
							<span><?php echo esc_html( $lyk7_phones[0][1][0] ); ?></span>
						</a>
					</li>
				<?php endif; ?>
				<?php if ( $lyk7_email ) : ?>
					<li>
						<a href="mailto:<?php echo esc_attr( antispambot( $lyk7_email ) ); ?>">
							<?php lyk7_icon( 'mail', 15 ); ?>
							<span><?php echo esc_html( antispambot( $lyk7_email ) ); ?></span>
						</a>
					</li>
				<?php endif; ?>
			</ul>
		</div>
	</div>

	<div class="masthead">
		<div class="wrap masthead__inner">

			<div class="brand">
				<?php if ( has_custom_logo() ) : ?>
					<div class="brand__logo"><?php the_custom_logo(); ?></div>
				<?php endif; ?>

				<div class="brand__text">
					<?php if ( is_front_page() ) : ?>
						<span class="brand__name"><?php bloginfo( 'name' ); ?></span>
					<?php else : ?>
						<a class="brand__name" href="<?php echo esc_url( home_url( '/' ) ); ?>" rel="home"><?php bloginfo( 'name' ); ?></a>
					<?php endif; ?>
					<?php if ( get_bloginfo( 'description' ) ) : ?>
						<span class="brand__tagline"><?php bloginfo( 'description' ); ?></span>
					<?php endif; ?>
				</div>
			</div>

			<nav class="primary-nav" id="primary-nav" aria-label="Κύρια πλοήγηση">
				<?php lyk7_nav( 'primary', 'menu' ); ?>
			</nav>

			<div class="masthead__actions">
				<button type="button" class="icon-button" id="search-toggle" aria-expanded="false" aria-controls="site-search">
					<?php lyk7_icon( 'search', 24 ); ?>
					<span class="screen-reader-text">Αναζήτηση</span>
				</button>

				<button type="button" class="icon-button nav-toggle" id="nav-toggle" aria-expanded="false" aria-controls="primary-nav">
					<span class="nav-toggle__bars" aria-hidden="true"><i></i><i></i><i></i></span>
					<span class="screen-reader-text">Μενού</span>
				</button>
			</div>

		</div>
	</div>

	<div class="site-search" id="site-search" hidden>
		<div class="wrap">
			<?php get_search_form(); ?>
		</div>
	</div>

</header>

<main id="content" class="site-main">
