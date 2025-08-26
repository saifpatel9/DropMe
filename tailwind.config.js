/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html', // Look in all HTML templates
    './**/templates/**/*.html', // Look in app-specific HTML templates
    './static/src/**/*.js', // If you have JavaScript files that add classes
    // Add any other paths where you use Tailwind classes
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}