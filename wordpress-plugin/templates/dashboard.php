<?php
/**
 * A³E Dashboard Template for WordPress
 */
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - A³E | <?php bloginfo('name'); ?></title>
    
    <!-- Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- WordPress Head -->
    <?php wp_head(); ?>
    
    <style>
        body { font-family: 'Inter', sans-serif; }
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Include the dashboard content from the HTML file -->
    <?php
    // Get the dashboard HTML content
    $dashboard_html = file_get_contents(dirname(__FILE__) . '/../../web/dashboard.html');
    
    // Extract just the body content (between <body> and </body>)
    preg_match('/<body[^>]*>(.*?)<\/body>/s', $dashboard_html, $matches);
    if (isset($matches[1])) {
        echo $matches[1];
    }
    ?>
    
    <?php wp_footer(); ?>
</body>
</html>
