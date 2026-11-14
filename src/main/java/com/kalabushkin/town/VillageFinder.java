package com.kalabushkin.town;

import java.util.Optional;

import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.tag.StructureTags;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.structure.StructureSet;
import net.minecraft.structure.StructureSetKeys;
import net.minecraft.structure.StructureStart;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.ChunkPos;
import net.minecraft.world.chunk.Chunk;
import net.minecraft.world.chunk.ChunkStatus;
import net.minecraft.world.gen.chunk.placement.RandomSpreadStructurePlacement;
import net.minecraft.world.gen.structure.Structure;

/** Finds villages by walking the grid they are generated on, like /locate does. */
public final class VillageFinder {
	/** How many grid cells to look through in each direction (a cell is 34 chunks in vanilla). */
	private static final int SEARCH_CELLS = 2;

	private VillageFinder() {
	}

	/** The centre of the nearest village at least {@code minDistance} blocks away from {@code from}. */
	public static Optional<BlockPos> nearestOther(ServerWorld world, BlockPos from, int minDistance) {
		StructureSet villages = world.getRegistryManager().get(RegistryKeys.STRUCTURE_SET).get(StructureSetKeys.VILLAGES);
		if (villages == null || !(villages.placement() instanceof RandomSpreadStructurePlacement placement)) {
			return Optional.empty();
		}
		Registry<Structure> structures = world.getRegistryManager().get(RegistryKeys.STRUCTURE);
		long seed = world.getChunkManager().getStructurePlacementCalculator().getStructureSeed();
		ChunkPos origin = new ChunkPos(from);
		BlockPos best = null;
		double bestDistance = Double.MAX_VALUE;
		for (int cellX = -SEARCH_CELLS; cellX <= SEARCH_CELLS; cellX++) {
			for (int cellZ = -SEARCH_CELLS; cellZ <= SEARCH_CELLS; cellZ++) {
				ChunkPos candidate = placement.getStartChunk(seed,
						origin.x + cellX * placement.getSpacing(), origin.z + cellZ * placement.getSpacing());
				// Only the structure starts are computed; no terrain is generated here.
				Chunk chunk = world.getChunk(candidate.x, candidate.z, ChunkStatus.STRUCTURE_STARTS);
				for (StructureStart start : chunk.getStructureStarts().values()) {
					if (!start.hasChildren() || !structures.getEntry(start.getStructure()).isIn(StructureTags.VILLAGE)) {
						continue;
					}
					BlockPos center = start.getBoundingBox().getCenter();
					double distance = Math.hypot(center.getX() - from.getX(), center.getZ() - from.getZ());
					if (distance >= minDistance && distance < bestDistance) {
						best = center;
						bestDistance = distance;
					}
				}
			}
		}
		return Optional.ofNullable(best);
	}
}
