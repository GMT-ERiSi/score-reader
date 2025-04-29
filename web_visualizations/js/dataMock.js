/**
 * dataMock.js
 * Provides dummy player stats data for testing additional leaderboards
 */

// Generate dummy player stats for testing additional leaderboards
function generateDummyPlayerStats() {
    // Use existing player data from pickup ELO if available
    // Access via window object since we're in a module
    const existingPlayers = (typeof window !== 'undefined' && window.pickupEloLadder) 
        ? window.pickupEloLadder 
        : [];
    
    const playerNames = existingPlayers.length > 0 
        ? existingPlayers.map(p => p.player_name) 
        : Array.from({ length: 10 }, (_, i) => `Player ${i + 1}`);
    
    console.log(`Generating stats for ${playerNames.length} players`, playerNames);
    
    const playerStats = [];
    
    playerNames.forEach((name, index) => {
        // Generate random but sensible stats for each player
        const matches = Math.floor(Math.random() * 15) + 5; // 5-20 matches
        
        // Skill level affects all stats (some players are better overall)
        const skillLevel = Math.random() * 0.5 + 0.5; // 0.5-1.0 skill factor
        
        // Different playstyles (some focus more on AI, some on players, etc.)
        const aiKillFocus = Math.random() * 0.5 + 0.75; // 0.75-1.25 AI kill factor
        const playerKillFocus = Math.random() * 0.5 + 0.75; // 0.75-1.25 player kill factor
        const damageFocus = Math.random() * 0.5 + 0.75; // 0.75-1.25 damage factor
        const defensiveFocus = 1.5 - (Math.random() * 0.5); // 1.0-1.5 survival factor (higher = fewer deaths)
        
        // Calculate base stats per match
        const baseAiKillsPerMatch = 8 * skillLevel * aiKillFocus;
        const basePlayerKillsPerMatch = 4 * skillLevel * playerKillFocus;
        const baseDeathsPerMatch = 5 * (1/skillLevel) * (1/defensiveFocus);
        const baseDamagePerMatch = 30000 * skillLevel * damageFocus;
        
        // Calculate total stats with some randomness
        const totalAiKills = Math.floor(baseAiKillsPerMatch * matches * (0.9 + Math.random() * 0.2));
        const totalPlayerKills = Math.floor(basePlayerKillsPerMatch * matches * (0.9 + Math.random() * 0.2));
        const totalDeaths = Math.floor(baseDeathsPerMatch * matches * (0.9 + Math.random() * 0.2));
        const totalDamage = Math.floor(baseDamagePerMatch * matches * (0.9 + Math.random() * 0.2));
        
        // Create player stats object
        playerStats.push({
            player_id: index + 1,
            player_name: name,
            matches_played: matches,
            ai_kills: totalAiKills,
            player_kills: totalPlayerKills,
            deaths: totalDeaths,
            total_damage: totalDamage,
            ai_kills_per_match: totalAiKills / matches,
            damage_per_match: totalDamage / matches
        });
    });
    
    return playerStats;
}

export { generateDummyPlayerStats };