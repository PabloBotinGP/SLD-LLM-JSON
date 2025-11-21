<?php

//Simple Fuzzy Matching using Jaro-Winkler Distance

class SimpleFuzzyMatcher {
    
    /**
     * Find best matches using Jaro-Winkler algorithm
     */
    public function findMatches($searchTerm, $companies, $maxResults = 5, $minScore = 0.6) {
        $results = [];
        
        $searchTerm = $this->normalize($searchTerm);
        
        foreach ($companies as $company) {
            $normalizedCompany = $this->normalize($company);
            $score = $this->jaroWinkler($searchTerm, $normalizedCompany);
            
            if ($score >= $minScore) {
                $results[] = [
                    'company' => $company,
                    'score' => round($score, 3)
                ];
            }
        }
        
        // Sort by score (best first)
        usort($results, fn($a, $b) => $b['score'] <=> $a['score']);
        
        return array_slice($results, 0, $maxResults);
    }
    
    /**
     * Normalize company name for better matching
     */
    private function normalize($str) {
        $str = strtolower(trim($str));
        
        // Remove common company suffixes
        $str = preg_replace('/\b(inc|llc|ltd|corp|co|technologies|tech)\b\.?/i', '', $str);
        
        // Clean up extra spaces
        $str = preg_replace('/\s+/', ' ', trim($str));
        
        return $str;
    }
    
    /**
     * Jaro-Winkler Distance
     */
    private function jaroWinkler($str1, $str2) {
        $jaro = $this->jaro($str1, $str2);
        
        if ($jaro < 0.7) {
            return $jaro;
        }
        
        // Give bonus for common prefix (up to 4 chars)
        $prefix = 0;
        $maxPrefix = min(4, strlen($str1), strlen($str2));
        
        for ($i = 0; $i < $maxPrefix; $i++) {
            if ($str1[$i] === $str2[$i]) {
                $prefix++;
            } else {
                break;
            }
        }
        
        return $jaro + (0.1 * $prefix * (1 - $jaro));
    }
    
    /**
     * Jaro Distance calculation
     */
    private function jaro($str1, $str2) {
        $len1 = strlen($str1);
        $len2 = strlen($str2);
        
        if ($len1 === 0 && $len2 === 0) return 1.0;
        if ($len1 === 0 || $len2 === 0) return 0.0;
        
        $matchWindow = max(0, (int)(max($len1, $len2) / 2) - 1);
        
        $str1Matches = array_fill(0, $len1, false);
        $str2Matches = array_fill(0, $len2, false);
        
        $matches = 0;
        
        // Find matches
        for ($i = 0; $i < $len1; $i++) {
            $start = max(0, $i - $matchWindow);
            $end = min($i + $matchWindow + 1, $len2);
            
            for ($j = $start; $j < $end; $j++) {
                if ($str2Matches[$j] || $str1[$i] !== $str2[$j]) {
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
        $transpositions = 0;
        $k = 0;
        
        for ($i = 0; $i < $len1; $i++) {
            if (!$str1Matches[$i]) continue;
            
            while (!$str2Matches[$k]) $k++;
            
            if ($str1[$i] !== $str2[$k]) {
                $transpositions++;
            }
            $k++;
        }
        
        return ($matches / $len1 + $matches / $len2 + ($matches - $transpositions / 2) / $matches) / 3;
    }
    
    /**
     * Display results nicely
     */
    public function showResults($searchTerm, $results) {
        echo "\n🔍 Searching for: '$searchTerm'\n";
        echo str_repeat("─", 50) . "\n";
        
        if (empty($results)) {
            echo "❌ No matches found\n";
            return;
        }
        
        foreach ($results as $i => $result) {
            $stars = str_repeat("★", (int)($result['score'] * 5));
            echo sprintf("%d. %s (%.3f) %s\n", 
                $i + 1, 
                $result['company'], 
                $result['score'],
                $stars
            );
        }
        echo "\n";
    }
}

// Test the simple matcher
$matcher = new SimpleFuzzyMatcher();

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

// Find and display matches
$results = $matcher->findMatches($searchTerm, $companies);
$matcher->showResults($searchTerm, $results);

// Test a few more variations
$testTerms = ['eco flow', 'EcoFlow Inc', 'ecoflw', 'Anker'];

foreach ($testTerms as $term) {
    $results = $matcher->findMatches($term, $companies, 3);
    $matcher->showResults($term, $results);
}

?>