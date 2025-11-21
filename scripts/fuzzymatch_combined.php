<?php

class FuzzyMatcher {
    
    private $weights = [
        'jaro_winkler' => 0.4,
        'levenshtein' => 0.3,
        'token_match' => 0.2,
        'soundex' => 0.1
    ];
    
    /**
     * Main fuzzy matching function
     * 
     * @param string $needle - The search string
     * @param array $haystack - Array of strings to search in
     * @param int $limit - Maximum number of results to return
     * @param float $threshold - Minimum similarity score (0-1)
     * @return array - Sorted array of matches with scores
     */
    public function fuzzyMatch($needle, $haystack, $limit = 5, $threshold = 0.3) {
        $results = [];
        
        // Normalize the search string
        $needle_clean = $this->normalizeString($needle);
        
        foreach ($haystack as $candidate) {
            $candidate_clean = $this->normalizeString($candidate);
            
            // Calculate composite score
            $score = $this->calculateCompositeScore($needle_clean, $candidate_clean);
            
            if ($score >= $threshold) {
                $results[] = [
                    'match' => $candidate,
                    'score' => $score,
                    'details' => $this->getScoreDetails($needle_clean, $candidate_clean)
                ];
            }
        }
        
        // Sort by score (highest first)
        usort($results, function($a, $b) {
            return $b['score'] <=> $a['score'];
        });
        
        return array_slice($results, 0, $limit);
    }
    
    /**
     * Calculate composite similarity score using multiple algorithms
     */
    private function calculateCompositeScore($str1, $str2) {
        $scores = [
            'jaro_winkler' => $this->jaroWinkler($str1, $str2),
            'levenshtein' => $this->normalizedLevenshtein($str1, $str2),
            'token_match' => $this->tokenBasedSimilarity($str1, $str2),
            'soundex' => $this->soundexSimilarity($str1, $str2)
        ];
        
        $compositeScore = 0;
        foreach ($scores as $algorithm => $score) {
            $compositeScore += $score * $this->weights[$algorithm];
        }
        
        return $compositeScore;
    }
    
    /**
     * Get detailed breakdown of similarity scores
     */
    private function getScoreDetails($str1, $str2) {
        return [
            'jaro_winkler' => round($this->jaroWinkler($str1, $str2), 3),
            'levenshtein' => round($this->normalizedLevenshtein($str1, $str2), 3),
            'token_match' => round($this->tokenBasedSimilarity($str1, $str2), 3),
            'soundex' => round($this->soundexSimilarity($str1, $str2), 3)
        ];
    }
    
    /**
     * Normalize string for comparison
     */
    private function normalizeString($str) {
        // Ensure input is a string
        $str = (string)$str;
        
        // Convert to lowercase
        $str = strtolower($str);
        
        // Remove common company suffixes/prefixes for better matching
        $patterns = [
            '/\b(inc|llc|ltd|corp|corporation|company|co|technologies|tech|energy|power|systems?|solutions?)\b\.?/',
            '/\b(the)\s+/',
        ];
        
        foreach ($patterns as $pattern) {
            $str = preg_replace($pattern, '', $str);
        }
        
        // Remove extra whitespace and punctuation
        $str = preg_replace('/[^\w\s]/', '', $str);
        $str = preg_replace('/\s+/', ' ', $str);
        $str = trim($str);
        
        return $str;
    }
    
    /**
     * Jaro-Winkler Distance implementation
     * Excellent for strings with common prefixes
     */
    private function jaroWinkler($str1, $str2) {
        // Ensure inputs are strings
        $str1 = (string)$str1;
        $str2 = (string)$str2;
        
        $jaro = $this->jaro($str1, $str2);
        
        if ($jaro < 0.7) {
            return $jaro;
        }
        
        // Calculate common prefix length (up to 4 characters)
        $prefix = 0;
        $maxPrefix = min(4, min(strlen($str1), strlen($str2)));
        
        for ($i = 0; $i < $maxPrefix; $i++) {
            if (isset($str1[$i]) && isset($str2[$i]) && $str1[$i] === $str2[$i]) {
                $prefix++;
            } else {
                break;
            }
        }
        
        return $jaro + (0.1 * $prefix * (1 - $jaro));
    }
    
    /**
     * Jaro Distance implementation
     */
    private function jaro($str1, $str2) {
        // Ensure inputs are strings
        $str1 = (string)$str1;
        $str2 = (string)$str2;
        
        $len1 = strlen($str1);
        $len2 = strlen($str2);
        
        if ($len1 === 0 && $len2 === 0) return 1.0;
        if ($len1 === 0 || $len2 === 0) return 0.0;
        
        $matchWindow = (int)(max($len1, $len2) / 2) - 1;
        if ($matchWindow < 0) $matchWindow = 0;
        
        $str1Matches = array_fill(0, $len1, false);
        $str2Matches = array_fill(0, $len2, false);
        
        $matches = 0;
        $transpositions = 0;
        
        // Find matches
        for ($i = 0; $i < $len1; $i++) {
            $start = max(0, (int)($i - $matchWindow));
            $end = min((int)($i + $matchWindow + 1), $len2);
            
            for ($j = $start; $j < $end; $j++) {
                if ($str2Matches[$j] || !isset($str1[$i]) || !isset($str2[$j]) || $str1[$i] !== $str2[$j]) {
                    continue;
                }
                
                $str1Matches[$i] = true;
                $str2Matches[$j] = true;
                $matches++;
                break;
            }
        }
        
        if ($matches === 0) return 0.0;
        
        // Count transpositions
        $k = 0;
        for ($i = 0; $i < $len1; $i++) {
            if (!$str1Matches[$i]) continue;
            
            while ($k < $len2 && !$str2Matches[$k]) $k++;
            
            if ($k < $len2 && isset($str1[$i]) && isset($str2[$k]) && $str1[$i] !== $str2[$k]) {
                $transpositions++;
            }
            $k++;
        }
        
        return ($matches / $len1 + $matches / $len2 + ($matches - $transpositions / 2) / $matches) / 3;
    }
    
    /**
     * Normalized Levenshtein Distance (returns similarity score 0-1)
     */
    private function normalizedLevenshtein($str1, $str2) {
        // Ensure inputs are strings
        $str1 = (string)$str1;
        $str2 = (string)$str2;
        
        $len1 = strlen($str1);
        $len2 = strlen($str2);
        $maxLen = max($len1, $len2);
        
        if ($maxLen === 0) return 1.0;
        
        $distance = levenshtein($str1, $str2);
        return 1 - ($distance / $maxLen);
    }
    
    /**
     * Token-based similarity for multi-word strings
     */
    private function tokenBasedSimilarity($str1, $str2) {
        $tokens1 = array_filter(explode(' ', $str1));
        $tokens2 = array_filter(explode(' ', $str2));
        
        if (empty($tokens1) && empty($tokens2)) return 1.0;
        if (empty($tokens1) || empty($tokens2)) return 0.0;
        
        $intersection = array_intersect($tokens1, $tokens2);
        $union = array_unique(array_merge($tokens1, $tokens2));
        
        // Jaccard similarity
        $jaccard = count($intersection) / count($union);
        
        // Also check for partial token matches
        $partialMatches = 0;
        $totalComparisons = 0;
        
        foreach ($tokens1 as $token1) {
            foreach ($tokens2 as $token2) {
                $totalComparisons++;
                $similarity = $this->normalizedLevenshtein($token1, $token2);
                if ($similarity > 0.7) {
                    $partialMatches += $similarity;
                }
            }
        }
        
        $partialScore = $totalComparisons > 0 ? $partialMatches / $totalComparisons : 0;
        
        // Combine Jaccard and partial matching
        return ($jaccard * 0.7) + ($partialScore * 0.3);
    }
    
    /**
     * Soundex-based phonetic similarity
     */
    private function soundexSimilarity($str1, $str2) {
        // For multi-word strings, compare soundex of each word
        $tokens1 = array_filter(explode(' ', $str1));
        $tokens2 = array_filter(explode(' ', $str2));
        
        if (empty($tokens1) && empty($tokens2)) return 1.0;
        if (empty($tokens1) || empty($tokens2)) return 0.0;
        
        $matches = 0;
        $totalComparisons = 0;
        
        foreach ($tokens1 as $token1) {
            foreach ($tokens2 as $token2) {
                $totalComparisons++;
                if (soundex($token1) === soundex($token2)) {
                    $matches++;
                }
            }
        }
        
        return $totalComparisons > 0 ? $matches / $totalComparisons : 0;
    }
    
    /**
     * Pretty print results
     */
    public function printResults($needle, $results) {
        echo "\n" . str_repeat("=", 60) . "\n";
        echo "FUZZY MATCH RESULTS FOR: '$needle'\n";
        echo str_repeat("=", 60) . "\n";
        
        if (empty($results)) {
            echo "No matches found.\n";
            return;
        }
        
        foreach ($results as $i => $result) {
            echo "\n" . ($i + 1) . ". {$result['match']}\n";
            echo "   Overall Score: " . round($result['score'], 3) . "\n";
            echo "   Breakdown:\n";
            foreach ($result['details'] as $algorithm => $score) {
                echo "     - " . ucfirst(str_replace('_', ' ', $algorithm)) . ": $score\n";
            }
        }
        
        echo "\n" . str_repeat("=", 60) . "\n";
    }
}

// Test data
$searchTerm = 'Ecoflow';

$companies = [
    'ABB',
    'AIMS Power Inc.',
    'Afore New Energy Technology (Shanghai) Co., Ltd.',
    'Alpha ESS Co., Ltd.',
    'Altenergy Power System Inc.',
    'Amensolar Ess Co., Ltd',
    'Anker Innovations Limited',
    'Aptos Solar Technology LLC',
    'CSI Solar Co., Ltd.',
    'Cherry Solution Co., Ltd.',
    'Chilicon Power, LLC',
    'Chint Power Systems America',
    'Darfon Electronics Corp.',
    'Delta Electronics',
    'Dyness Digital Energy Technology Co., LTD.',
    'EG4 Electronics LLC',
    'EPC Power Corp.',
    'EcoFlow Inc.',
    'Energizer Solar',
    'Enphase Energy, Inc.',
    'FOXESS CO., LTD.',
    'Fortress Power LLC',
    'FranklinWH Energy Storage Inc.',
    'Fronius International GmbH',
    'Generac Power Systems, Inc.',
    'General Motors Energy LLC',
    'Geneverse Energy Inc.',
    'Ginlong Technologies Co., Ltd.',
    'GoodWe Technologies Co., Ltd.'
];

// Run the fuzzy matching
$matcher = new FuzzyMatcher();
$results = $matcher->fuzzyMatch($searchTerm, $companies, 3, 0.2);

// Display results
$matcher->printResults($searchTerm, $results);

// Additional test with different search terms
// echo "\n\n" . str_repeat("*", 60) . "\n";
// echo "TESTING WITH DIFFERENT VARIATIONS:\n";
// echo str_repeat("*", 60) . "\n";

// $testTerms = ['eco flow', 'ecoflw', 'eco-flow', 'EcoFlow Inc'];

// foreach ($testTerms as $term) {
//     $results = $matcher->fuzzyMatch($term, $companies, 3, 0.3);
//     echo "\nSearch: '$term' -> Top match: ";
//     if (!empty($results)) {
//         echo "'{$results[0]['match']}' (Score: " . round($results[0]['score'], 3) . ")\n";
//     } else {
//         echo "No matches found\n";
//     }
// }

?>
