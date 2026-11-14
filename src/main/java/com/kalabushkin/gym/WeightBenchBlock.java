package com.kalabushkin.gym;

import com.mojang.serialization.MapCodec;

import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.block.HorizontalFacingBlock;
import net.minecraft.block.ShapeContext;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemPlacementContext;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.state.StateManager;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.world.BlockView;
import net.minecraft.world.World;

/** Use it with a barbell in the main hand to bench press. */
public class WeightBenchBlock extends HorizontalFacingBlock {
	public static final MapCodec<WeightBenchBlock> CODEC = createCodec(WeightBenchBlock::new);
	private static final VoxelShape SHAPE = Block.createCuboidShape(0, 0, 0, 16, 8, 16);
	private static final int REP_COOLDOWN = 25;

	public WeightBenchBlock(Settings settings) {
		super(settings);
		setDefaultState(getDefaultState().with(FACING, net.minecraft.util.math.Direction.NORTH));
	}

	@Override
	protected MapCodec<? extends HorizontalFacingBlock> getCodec() {
		return CODEC;
	}

	@Override
	protected void appendProperties(StateManager.Builder<Block, BlockState> builder) {
		builder.add(FACING);
	}

	@Override
	public BlockState getPlacementState(ItemPlacementContext ctx) {
		return getDefaultState().with(FACING, ctx.getHorizontalPlayerFacing().getOpposite());
	}

	@Override
	protected VoxelShape getOutlineShape(BlockState state, BlockView world, BlockPos pos, ShapeContext context) {
		return SHAPE;
	}

	@Override
	protected ActionResult onUse(BlockState state, World world, BlockPos pos, PlayerEntity player, BlockHitResult hit) {
		if (!player.getMainHandStack().isOf(GymContent.BARBELL)) {
			if (!world.isClient) {
				player.sendMessage(Text.translatable("gym.kalabushkin.need_barbell"), true);
			}
			return ActionResult.success(world.isClient);
		}
		if (player.getItemCooldownManager().isCoolingDown(GymContent.BARBELL)) {
			return ActionResult.CONSUME;
		}
		if (player instanceof ServerPlayerEntity serverPlayer) {
			Gym.rep(serverPlayer, Exercise.BENCH);
		}
		player.getItemCooldownManager().set(GymContent.BARBELL, REP_COOLDOWN);
		return ActionResult.success(world.isClient);
	}
}
