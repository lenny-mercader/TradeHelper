/** Groups countries by continent for the catalogue's filter accordion: checking a continent
 * selects every one of its countries that's actually present in the data. */
export const CONTINENTS: { name: string; countries: string[] }[] = [
  {
    name: 'Europe',
    countries: [
      'France',
      'Germany',
      'United Kingdom',
      'Spain',
      'Italy',
      'Netherlands',
      'Switzerland',
      'Ireland',
      'Luxembourg',
      'Belgium',
      'Sweden',
      'Denmark',
      'Norway',
      'Finland',
      'Austria',
      'Poland',
      'Portugal',
      'Greece',
      'Czech Republic',
      'Hungary',
      'Romania',
    ],
  },
  {
    name: 'Amérique du Nord',
    countries: ['United States', 'Canada', 'Mexico'],
  },
  {
    name: 'Asie',
    countries: [
      'Japan',
      'South Korea',
      'China',
      'Hong Kong',
      'Taiwan',
      'India',
      'Singapore',
      'Israel',
    ],
  },
  {
    name: 'Océanie',
    countries: ['Australia', 'New Zealand'],
  },
  {
    name: 'Amérique du Sud',
    countries: ['Brazil', 'Argentina', 'Chile', 'Colombia'],
  },
]
