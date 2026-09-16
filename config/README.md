# Sharded config

Watches are split across 6 files so the workflow can check them in
parallel (6 separate GitHub Actions jobs, one per file) instead of one
job checking everything. Each shard file has the same structure as a
single combined config would (`listing_watches` / `stock_watches`) -
sharding only changes *which file* a watch lives in, not the format.

| Shard | Stores |
|---|---|
| `shard-1.json` | Big W, JB Hi-Fi |
| `shard-2.json` | Target, Toymate, Kidstuff |
| `shard-3.json` | Mr Toys, Grailborne, Drop Store |
| `shard-4.json` | Kmart, Toyworld, Pokémon Center Australia, Amazon |
| `shard-5.json` | EB Games, Zing Pop Culture, Collectible Madness, Good Games |
| `shard-6.json` | PokeSource AU, Unplugged Games, Toys "R" Us Australia, Milsims Games, Games World, Gameology, Trainer Town |

## Adding a new watch

Pick whichever shard file has the fewest entries right now (roughly
balanced load matters more than which retailers end up grouped
together), add your entry to its `listing_watches` or `stock_watches`
array the same way you would in a single config file, commit, and
push. No workflow changes needed - each shard's job already loops over
whatever is in its file.

## Adding a whole new shard (e.g. shard-7)

Only worth doing if the existing 6 get too large/slow individually:

1. Create `config/shard-7.json` (same structure as the others) and
   `state/shard-7.json` containing just `{}`.
2. In `.github/workflows/check-stock.yml`, add `7` to the
   `matrix.shard` list (`[1, 2, 3, 4, 5, 6, 7]`).

That's it - the rest of the workflow already parameterizes everything
else (config path, state path, concurrency group) off `matrix.shard`.
